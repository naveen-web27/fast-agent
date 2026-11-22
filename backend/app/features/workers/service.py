"""Local workforce hub: worker profiles, employer-verified skills, hires, reviews, job posts and admin-added workers.

Trust model: a worker's own skills are shown as self-declared. A skill becomes employer-verified only when an
admin of a RightConnect-verified company confirms (or adds) a job in the worker's history that lists it.
"""
import hashlib
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, case, delete, exists, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core.location import proximity, proximity_rank
from app.core.plans import CONTACT_DAILY_LIMIT, company_plan_active, expert_plan_active, plan_expiry
from app.features.marketplace.catalog import search_terms
from app.features.workers.schemas import (
    AdminContactReportOut,
    AdminWorkerCreate,
    AdminWorkerOut,
    AvailabilityUpdate,
    ClaimCodeOut,
    Contact,
    ContactViewOut,
    DirectContact,
    EmployerExperienceCreate,
    ExperienceConfirm,
    ExperienceCreate,
    ExperienceOut,
    HireCreate,
    HireOut,
    HiresResponse,
    JobApply,
    JobCreate,
    JobOut,
    LinkProfile,
    LocationUpdate,
    MyWorkerProfile,
    ReviewCreate,
    SkillOut,
    VerificationRequestOut,
    WorkerCreate,
    WorkerDetail,
    WorkerLinkOut,
    WorkerListResponse,
    WorkerReviewOut,
    WorkerSummary,
    WorkerUpdate,
)
from app.models.admin_action import AdminAction
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, Profile, ProfileKind, VerificationStatus
from app.models.user import SubscriptionTier, User, UserRole, active_user_by_auth_id
from app.models.worker import (
    Availability,
    ExperienceStatus,
    HireStatus,
    JobPost,
    WorkerContactView,
    WorkerExperience,
    WorkerHire,
    WorkerProfile,
    WorkerReview,
)

STALE_AFTER_DAYS = 14
CLAIM_CODE_DAYS = 30
CLAIM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
INDIA_TIME = timezone(timedelta(hours=5, minutes=30))


class WorkerNotFoundError(Exception):
    """The worker, job, hire or experience doesn't exist or isn't visible to the caller."""


class WorkerAccessError(Exception):
    """The caller isn't allowed to do this (not the worker, not the employer, not a company admin)."""


class WorkerConflictError(Exception):
    """Duplicate profile/request, wrong state for this action, or a claim that can't be used."""


class WorkerIdentityError(Exception):
    """The caller hasn't finished creating their RightConnect account."""


class WorkerLimitError(Exception):
    """The caller has used today's worker contacts for their plan."""


# ---------- pure helpers (unit-tested) ----------


def effective_availability(availability: str, busy_until: date | None, today: date) -> str:
    """A worker who was busy until a date that has passed is free again."""
    if availability == Availability.BUSY.value and busy_until is not None and busy_until < today:
        return Availability.AVAILABLE.value
    return availability


def availability_is_stale(availability: str, updated_at: datetime | None, now: datetime) -> bool:
    return availability == Availability.AVAILABLE.value and (
        updated_at is None or now - updated_at > timedelta(days=STALE_AFTER_DAYS)
    )


def build_skills(self_skills: list[str], experiences: list[tuple[list[str], str, bool, str | None]]) -> list[SkillOut]:
    """Merge self-declared skills with skills from work history.

    experiences: (skills, status, employer_is_verified_company, employer_name). Only a VERIFIED experience from a
    verified company makes a skill verified; anything else counts as self-declared. Verified skills come first."""
    order: list[str] = []
    names: dict[str, str] = {}
    verified_by: dict[str, list[str]] = {}
    declared: set[str] = set()

    def note(skill: str) -> str:
        key = skill.lower()
        if key not in names:
            names[key] = skill
            order.append(key)
        return key

    for skills, status, company_verified, employer in experiences:
        if status == ExperienceStatus.DECLINED.value:
            continue
        for skill in skills:
            key = note(skill)
            if status == ExperienceStatus.VERIFIED.value and company_verified and employer:
                if employer not in verified_by.setdefault(key, []):
                    verified_by[key].append(employer)
            else:
                declared.add(key)
    for skill in self_skills:
        declared.add(note(skill))
    result = [
        SkillOut(name=names[key], verified=bool(verified_by.get(key)), verified_by=verified_by.get(key, []), self_declared=key in declared)
        for key in order
    ]
    return sorted(result, key=lambda skill: not skill.verified)


def hire_action_allowed(status: str, initiated_by: str, side: str, action: str) -> bool:
    """Who may move a hire forward: the side that didn't ask answers; the asker may withdraw; employers finish."""
    if action in ("accept", "decline"):
        return status == HireStatus.PENDING.value and side != initiated_by
    if action == "cancel":
        return (status == HireStatus.PENDING.value and side == initiated_by) or status == HireStatus.ACCEPTED.value
    if action == "complete":
        return status == HireStatus.ACCEPTED.value and side == "employer"
    return False


def generate_claim_code() -> str:
    raw = "".join(secrets.choice(CLAIM_CODE_ALPHABET) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def normalize_claim_code(code: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", code.upper())


def hash_claim_code(code: str) -> str:
    return hashlib.sha256(normalize_claim_code(code).encode()).hexdigest()


def india_day_start(now: datetime) -> datetime:
    """Midnight India time for the day `now` falls in; daily contact limits reset then."""
    return now.astimezone(INDIA_TIME).replace(hour=0, minute=0, second=0, microsecond=0)


def contact_limit_message(limit: int) -> str:
    upgrade = {
        CONTACT_DAILY_LIMIT[SubscriptionTier.FREE]: (
            f" Pro gives {CONTACT_DAILY_LIMIT[SubscriptionTier.PRO]} a day and Enterprise "
            f"{CONTACT_DAILY_LIMIT[SubscriptionTier.ENTERPRISE]}: see the Plans page."
        ),
        CONTACT_DAILY_LIMIT[SubscriptionTier.PRO]: (
            f" Enterprise gives {CONTACT_DAILY_LIMIT[SubscriptionTier.ENTERPRISE]} a day: see the Plans page."
        ),
    }.get(limit, "")
    return (
        f"You've opened {limit} new worker contacts today, the most for your plan. "
        f"It resets at midnight, and you can still send hire requests.{upgrade}"
    )


def merge_profile_fields(target: WorkerProfile, source: WorkerProfile) -> None:
    """Fill the account profile's gaps from the admin-made one; the worker's own entries win."""
    for field in ("bio", "city", "area", "pincode", "avatar_url", "contact_email", "contact_phone"):
        if not getattr(target, field) and getattr(source, field):
            setattr(target, field, getattr(source, field))
    if source.years_experience is not None and (target.years_experience is None or source.years_experience > target.years_experience):
        target.years_experience = source.years_experience
    if target.rate_amount is None and source.rate_amount is not None:
        target.rate_amount, target.rate_max = source.rate_amount, source.rate_max
        target.rate_unit, target.rate_hidden = source.rate_unit, source.rate_hidden
    for field, limit in (("skills", 25), ("languages", 10)):
        merged, seen = [], set()
        for item in [*(getattr(target, field) or []), *(getattr(source, field) or [])]:
            if item.lower() not in seen:
                seen.add(item.lower())
                merged.append(item)
        setattr(target, field, merged[:limit])
    total = (target.review_count or 0) + (source.review_count or 0)
    if total:
        weighted = float(target.average_rating or 0) * (target.review_count or 0) + float(source.average_rating or 0) * (source.review_count or 0)
        target.average_rating = round(weighted / total, 1)
    target.review_count = total


# ---------- shared lookups ----------


def generate_link_key() -> str:
    return secrets.token_urlsafe(18)


def hash_link_key(key: str) -> str:
    return hashlib.sha256(key.strip().encode()).hexdigest()


def reachable(worker: WorkerProfile) -> bool:
    """The worker can see and answer requests: through an account or a personal link."""
    return worker.user_id is not None or worker.access_key_hash is not None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _visible():
    """Live worker profiles whose owner (if any) isn't deleted or blocked."""
    owner_ok = or_(
        WorkerProfile.user_id.is_(None),
        exists().where(User.id == WorkerProfile.user_id, User.deleted_at.is_(None), User.blocked_at.is_(None)),
    )
    return and_(WorkerProfile.deleted_at.is_(None), WorkerProfile.blocked_at.is_(None), owner_ok)


def _effectively_available():
    return or_(
        WorkerProfile.availability == Availability.AVAILABLE.value,
        and_(
            WorkerProfile.availability == Availability.BUSY.value,
            WorkerProfile.busy_until.is_not(None),
            WorkerProfile.busy_until < func.current_date(),
        ),
    )


async def _user(session: AsyncSession, auth_user_id: UUID) -> User:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None:
        raise WorkerIdentityError("Finish creating your RightConnect account first")
    return user


async def _my_worker(session: AsyncSession, user: User) -> WorkerProfile | None:
    return await session.scalar(
        select(WorkerProfile).where(WorkerProfile.user_id == user.id, WorkerProfile.deleted_at.is_(None))
    )


async def _admin_org_ids(session: AsyncSession, user_id: UUID) -> set[UUID]:
    rows = await session.scalars(
        select(OrganizationMember.organization_id)
        .join(Organization, Organization.id == OrganizationMember.organization_id)
        .where(
            OrganizationMember.user_id == user_id,
            OrganizationMember.member_role == MemberRole.ADMIN.value,
            Organization.deleted_at.is_(None),
        )
    )
    return set(rows.all())


async def _visible_worker(session: AsyncSession, worker_id: UUID) -> WorkerProfile:
    worker = await session.scalar(select(WorkerProfile).where(WorkerProfile.id == worker_id, _visible()))
    if worker is None:
        raise WorkerNotFoundError("This worker profile could not be found")
    return worker


async def _experience_rows(session: AsyncSession, worker_ids: list[UUID]) -> dict[UUID, list[tuple]]:
    """worker_id -> [(experience, organization_name, organization_verified)] in one query."""
    if not worker_ids:
        return {}
    rows = (
        await session.execute(
            select(WorkerExperience, Organization.name, Organization.verification)
            .outerjoin(Organization, Organization.id == WorkerExperience.organization_id)
            .where(WorkerExperience.worker_id.in_(worker_ids))
            .order_by(WorkerExperience.start_date.desc().nulls_last(), WorkerExperience.created_at.desc())
        )
    ).all()
    grouped: dict[UUID, list[tuple]] = {}
    for experience, org_name, org_verification in rows:
        grouped.setdefault(experience.worker_id, []).append(
            (experience, org_name, org_verification == VerificationStatus.VERIFIED)
        )
    return grouped


def _experience_out(experience: WorkerExperience, org_name: str | None, org_verified: bool) -> ExperienceOut:
    return ExperienceOut(
        id=experience.id,
        employer_name=org_name or experience.employer_name,
        organization_id=experience.organization_id,
        role_title=experience.role_title,
        start_date=experience.start_date,
        end_date=experience.end_date,
        description=experience.description,
        skills=experience.skills,
        status=experience.status,
        added_by=experience.added_by,
        employer_verified=experience.status == ExperienceStatus.VERIFIED.value and org_verified,
        verified_at=experience.verified_at,
    )


def pay_fields(worker: WorkerProfile, include_private: bool) -> dict:
    """Hidden pay is left out of everything except the worker's own profile."""
    show = include_private or not worker.rate_hidden
    return {
        "rate_amount": worker.rate_amount if show else None,
        "rate_max": worker.rate_max if show else None,
        "rate_unit": worker.rate_unit if show else None,
        "rate_hidden": bool(worker.rate_hidden),
    }


def _summary(worker: WorkerProfile, experiences: list[tuple], include_private: bool = False) -> WorkerSummary:
    today = date.today()
    skills = build_skills(
        worker.skills,
        [(exp.skills, exp.status, org_verified, org_name or exp.employer_name) for exp, org_name, org_verified in experiences],
    )
    availability = effective_availability(worker.availability, worker.busy_until, today)
    return WorkerSummary(
        id=worker.id,
        display_name=worker.display_name,
        headline=worker.headline,
        city=worker.city,
        area=worker.area,
        pincode=worker.pincode,
        languages=worker.languages,
        years_experience=worker.years_experience,
        **pay_fields(worker, include_private),
        contact_available=bool(worker.show_contact) and (worker.user_id is not None or bool(worker.contact_phone or worker.contact_email)),
        availability=availability,
        busy_until=worker.busy_until if availability == Availability.BUSY.value else None,
        availability_stale=availability_is_stale(availability, worker.availability_updated_at, _now()),
        avatar_url=worker.avatar_url,
        average_rating=float(worker.average_rating or 0),
        review_count=worker.review_count,
        verified_skill_count=sum(1 for skill in skills if skill.verified),
        skills=skills,
        claimed=reachable(worker),
    )


async def _detail_fields(session: AsyncSession, worker: WorkerProfile, include_private: bool) -> dict:
    experiences = (await _experience_rows(session, [worker.id])).get(worker.id, [])
    review_rows = (
        await session.execute(
            select(WorkerReview, User.full_name)
            .join(User, User.id == WorkerReview.reviewer_id)
            .where(WorkerReview.worker_id == worker.id)
            .order_by(WorkerReview.created_at.desc())
            .limit(50)
        )
    ).all()
    shown = experiences if include_private else [row for row in experiences if row[0].status != ExperienceStatus.DECLINED.value]
    return {
        **_summary(worker, experiences, include_private).model_dump(),
        "bio": worker.bio,
        "experiences": [_experience_out(*row) for row in shown],
        "reviews": [
            WorkerReviewOut(reviewer_name=name, rating=review.rating, body=review.body, created_at=review.created_at)
            for review, name in review_rows
        ],
        "member_since": worker.claimed_at or worker.created_at,
    }


# ---------- public browsing ----------


async def search_workers(
    session: AsyncSession,
    query: str | None,
    city: str | None,
    area: str | None,
    available_only: bool,
    page: int,
    page_size: int,
    near_pincode: str | None = None,
    near_city: str | None = None,
) -> WorkerListResponse:
    stmt = select(WorkerProfile).where(_visible())
    if query:
        words, services = search_terms(query)
        conditions = []
        for word in [*words, *services]:
            pattern = _like(word)
            conditions.extend([
                WorkerProfile.display_name.ilike(pattern, escape="\\"),
                WorkerProfile.headline.ilike(pattern, escape="\\"),
                WorkerProfile.bio.ilike(pattern, escape="\\"),
                func.array_to_string(WorkerProfile.skills, " ").ilike(pattern, escape="\\"),
                exists().where(
                    WorkerExperience.worker_id == WorkerProfile.id,
                    WorkerExperience.status != ExperienceStatus.DECLINED.value,
                    or_(
                        WorkerExperience.role_title.ilike(pattern, escape="\\"),
                        func.array_to_string(WorkerExperience.skills, " ").ilike(pattern, escape="\\"),
                    ),
                ),
            ])
        if conditions:
            stmt = stmt.where(or_(*conditions))
    if city:
        stmt = stmt.where(WorkerProfile.city.ilike(_like(city), escape="\\"))
    if area:
        stmt = stmt.where(WorkerProfile.area.ilike(_like(area), escape="\\"))
    if available_only:
        stmt = stmt.where(_effectively_available())

    total = (await session.scalar(select(func.count()).select_from(stmt.subquery()))) or 0
    light = case(
        (_effectively_available(), 0),
        (WorkerProfile.availability == Availability.BUSY.value, 1),
        else_=2,
    )
    ordering = [light, WorkerProfile.user_id.is_(None), WorkerProfile.average_rating.desc(), WorkerProfile.availability_updated_at.desc()]
    # A free worker in another state can't help, so distance comes before the availability light.
    nearness = proximity_rank(WorkerProfile.pincode, WorkerProfile.city, near_pincode, near_city)
    if nearness is not None:
        ordering.insert(0, nearness.desc())
    workers = (
        await session.scalars(
            stmt.order_by(*ordering)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).all()
    experiences = await _experience_rows(session, [worker.id for worker in workers])
    results = [_summary(worker, experiences.get(worker.id, [])) for worker in workers]
    if nearness is not None:
        for worker, summary in zip(workers, results):
            summary.nearness = proximity(worker.pincode, worker.city, near_pincode, near_city)
    return WorkerListResponse(
        results=results,
        total=total,
        page=page,
        page_size=page_size,
    )


async def contact_daily_limit(session: AsyncSession, user: User) -> int | None:
    """New worker contacts the user may open per day: the best of their active plans (None = no limit)."""
    if user.role == UserRole.PLATFORM_ADMIN:
        return None
    tiers = {SubscriptionTier.FREE}
    if plan_expiry(user.subscription_tier, user.subscription_expires_at):
        tiers.add(SubscriptionTier(user.subscription_tier))
    expert = await session.scalar(
        select(Profile).where(Profile.user_id == user.id, Profile.kind == ProfileKind.EXPERT, Profile.deleted_at.is_(None))
    )
    if expert is not None and expert_plan_active(expert):
        tiers.add(SubscriptionTier.PRO)
    organizations = (
        await session.scalars(
            select(Organization)
            .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
            .where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.member_role == MemberRole.ADMIN.value,
                Organization.deleted_at.is_(None),
            )
        )
    ).all()
    if any(company_plan_active(organization) for organization in organizations):
        tiers.add(SubscriptionTier.ENTERPRISE)
    return max(CONTACT_DAILY_LIMIT[tier] for tier in tiers)


async def worker_contact(session: AsyncSession, auth_user_id: UUID, worker_id: UUID) -> DirectContact:
    """The worker's phone/WhatsApp/email for a signed-in user. Each view is logged for the worker to see, and
    opening a new worker counts toward the viewer's daily limit (opening the same worker again is free)."""
    user = await _user(session, auth_user_id)
    worker = await _visible_worker(session, worker_id)
    if not worker.show_contact:
        raise WorkerAccessError("This worker shares their number after you send a hire request and they accept.")
    owner = await session.get(User, worker.user_id) if worker.user_id else None
    phone = worker.contact_phone or (owner.phone if owner else None)
    email = worker.contact_email or (owner.email if owner else None)
    if not phone and not email:
        raise WorkerNotFoundError("This worker hasn't added a phone number yet. Send a hire request instead.")
    if worker.user_id == user.id:
        return DirectContact(name=worker.display_name, phone=phone, email=email)
    limit = await contact_daily_limit(session, user)
    # Locking the viewer's row makes two quick clicks wait for each other, so the limit can't be passed.
    await session.scalar(select(User.id).where(User.id == user.id).with_for_update())
    view = await session.scalar(
        select(WorkerContactView)
        .where(WorkerContactView.worker_id == worker.id, WorkerContactView.viewer_user_id == user.id)
        .with_for_update()
    )
    now = _now()
    used = (
        await session.scalar(
            select(func.count())
            .select_from(WorkerContactView)
            .where(WorkerContactView.viewer_user_id == user.id, WorkerContactView.first_viewed_at >= india_day_start(now))
        )
    ) or 0
    if view is None:
        if limit is not None and used >= limit:
            raise WorkerLimitError(contact_limit_message(limit))
        session.add(WorkerContactView(worker_id=worker.id, viewer_user_id=user.id, first_viewed_at=now, last_viewed_at=now, view_count=1))
        used += 1
    else:
        view.last_viewed_at = now
        view.view_count += 1
    await session.commit()
    return DirectContact(
        name=worker.display_name, phone=phone, email=email,
        daily_limit=limit, left_today=None if limit is None else max(limit - used, 0),
    )


async def _contact_views(session: AsyncSession, worker_id: UUID) -> list[ContactViewOut]:
    rows = (
        await session.execute(
            select(WorkerContactView, User.full_name)
            .join(User, User.id == WorkerContactView.viewer_user_id)
            .where(WorkerContactView.worker_id == worker_id)
            .order_by(WorkerContactView.last_viewed_at.desc())
            .limit(50)
        )
    ).all()
    companies: dict[UUID, str] = {}
    viewer_ids = [view.viewer_user_id for view, _ in rows]
    if viewer_ids:
        company_rows = await session.execute(
            select(OrganizationMember.user_id, Organization.name)
            .join(Organization, Organization.id == OrganizationMember.organization_id)
            .where(
                OrganizationMember.user_id.in_(viewer_ids),
                OrganizationMember.member_role == MemberRole.ADMIN.value,
                Organization.deleted_at.is_(None),
            )
        )
        for user_id, name in company_rows.all():
            companies.setdefault(user_id, name)
    return [
        ContactViewOut(
            id=view.id, viewer_name=name, company_name=companies.get(view.viewer_user_id),
            first_viewed_at=view.first_viewed_at, last_viewed_at=view.last_viewed_at,
            view_count=view.view_count, reported=view.reported_at is not None,
        )
        for view, name in rows
    ]


async def _report_view(session: AsyncSession, worker: WorkerProfile, view_id: UUID, reason: str) -> None:
    view = await session.get(WorkerContactView, view_id, with_for_update=True)
    if view is None or view.worker_id != worker.id:
        raise WorkerNotFoundError("This entry could not be found")
    view.reported_at = _now()
    view.report_reason = reason
    await session.commit()


async def my_contact_views(session: AsyncSession, auth_user_id: UUID) -> list[ContactViewOut]:
    user = await _user(session, auth_user_id)
    worker = await _my_worker(session, user)
    if worker is None:
        raise WorkerNotFoundError("Create your work profile first")
    return await _contact_views(session, worker.id)


async def report_my_contact_view(session: AsyncSession, auth_user_id: UUID, view_id: UUID, reason: str) -> list[ContactViewOut]:
    user = await _user(session, auth_user_id)
    worker = await _my_worker(session, user)
    if worker is None:
        raise WorkerNotFoundError("Create your work profile first")
    await _report_view(session, worker, view_id, reason)
    return await _contact_views(session, worker.id)


async def get_worker(session: AsyncSession, worker_id: UUID) -> WorkerDetail:
    worker = await _visible_worker(session, worker_id)
    return WorkerDetail(**await _detail_fields(session, worker, include_private=False))


# ---------- the worker's own profile ----------


async def _my_profile_out(session: AsyncSession, worker: WorkerProfile, user: User) -> MyWorkerProfile:
    return MyWorkerProfile(
        **await _detail_fields(session, worker, include_private=True),
        contact_phone=worker.contact_phone or user.phone,
        contact_email=worker.contact_email or user.email,
        show_contact=bool(worker.show_contact),
        self_skills=worker.skills,
    )


async def get_my_worker(session: AsyncSession, auth_user_id: UUID) -> MyWorkerProfile | None:
    user = await _user(session, auth_user_id)
    worker = await _my_worker(session, user)
    return await _my_profile_out(session, worker, user) if worker else None


def _apply_fields(worker: WorkerProfile, payload) -> None:
    worker.headline = payload.headline
    worker.bio = payload.bio
    worker.city = payload.city
    worker.area = payload.area
    worker.pincode = payload.pincode
    worker.languages = payload.languages
    worker.years_experience = payload.years_experience
    worker.skills = payload.skills
    worker.rate_amount = payload.rate_amount
    worker.rate_max = payload.rate_max
    worker.rate_unit = payload.rate_unit
    worker.rate_hidden = payload.rate_hidden
    if payload.contact_phone:
        worker.contact_phone = payload.contact_phone
    worker.show_contact = payload.show_contact


def new_worker_for_user(user: User, payload: WorkerCreate) -> WorkerProfile:
    worker = WorkerProfile(
        user_id=user.id,
        display_name=user.full_name,
        contact_phone=user.phone,
        availability=Availability.AVAILABLE.value,
        availability_updated_at=_now(),
        claim_status="claimed",
        claimed_at=_now(),
        adult_confirmed_at=_now(),
    )
    _apply_fields(worker, payload)
    return worker


async def create_my_worker(session: AsyncSession, auth_user_id: UUID, payload: WorkerCreate) -> MyWorkerProfile:
    user = await _user(session, auth_user_id)
    if await _my_worker(session, user):
        raise WorkerConflictError("You already have a worker profile")
    worker = new_worker_for_user(user, payload)
    session.add(worker)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError("You already have a worker profile") from exc
    return await _my_profile_out(session, worker, user)


async def _require_my_worker(session: AsyncSession, auth_user_id: UUID) -> tuple[User, WorkerProfile]:
    user = await _user(session, auth_user_id)
    worker = await _my_worker(session, user)
    if worker is None:
        raise WorkerNotFoundError("Create your worker profile first")
    return user, worker


async def update_my_worker(session: AsyncSession, auth_user_id: UUID, payload: WorkerUpdate) -> MyWorkerProfile:
    user, worker = await _require_my_worker(session, auth_user_id)
    _apply_fields(worker, payload)
    await session.commit()
    return await _my_profile_out(session, worker, user)


async def set_my_availability(session: AsyncSession, auth_user_id: UUID, payload: AvailabilityUpdate) -> MyWorkerProfile:
    user, worker = await _require_my_worker(session, auth_user_id)
    if payload.availability == Availability.BUSY.value and payload.busy_until and payload.busy_until < date.today():
        raise WorkerConflictError("The 'busy until' date has already passed")
    worker.availability = payload.availability
    worker.busy_until = payload.busy_until
    worker.availability_updated_at = _now()
    await session.commit()
    return await _my_profile_out(session, worker, user)


async def set_my_location(session: AsyncSession, auth_user_id: UUID, payload: LocationUpdate) -> MyWorkerProfile:
    user, worker = await _require_my_worker(session, auth_user_id)
    worker.pincode = payload.pincode
    # A new place replaces the old area name; city is kept only when the picker didn't know it.
    worker.area = payload.area
    if payload.city:
        worker.city = payload.city
    await session.commit()
    return await _my_profile_out(session, worker, user)


async def add_my_experience(session: AsyncSession, auth_user_id: UUID, payload: ExperienceCreate) -> MyWorkerProfile:
    """Worker-added history: confirmed later by the company if it's on RightConnect, otherwise self-declared."""
    user, worker = await _require_my_worker(session, auth_user_id)
    employer_name = payload.employer_name
    status = ExperienceStatus.SELF.value
    if payload.organization_id:
        organization = await session.get(Organization, payload.organization_id)
        if organization is None or organization.deleted_at is not None:
            raise WorkerNotFoundError("That company could not be found")
        employer_name = organization.name
        status = ExperienceStatus.PENDING.value
    session.add(
        WorkerExperience(
            worker_id=worker.id,
            organization_id=payload.organization_id,
            employer_name=employer_name,
            role_title=payload.role_title,
            start_date=payload.start_date,
            end_date=payload.end_date,
            description=payload.description,
            skills=payload.skills,
            status=status,
            added_by="worker",
        )
    )
    await session.commit()
    return await _my_profile_out(session, worker, user)


async def delete_my_experience(session: AsyncSession, auth_user_id: UUID, experience_id: UUID) -> MyWorkerProfile:
    """Workers control their own profile, so they can remove any entry, including employer-added ones."""
    user, worker = await _require_my_worker(session, auth_user_id)
    experience = await session.get(WorkerExperience, experience_id)
    if experience is None or experience.worker_id != worker.id:
        raise WorkerNotFoundError("This work history entry could not be found")
    await session.delete(experience)
    await session.commit()
    return await _my_profile_out(session, worker, user)


async def claim_worker_profile(session: AsyncSession, auth_user_id: UUID, code: str) -> MyWorkerProfile:
    """Take over an admin-added profile with the one-time code RightConnect gave the worker."""
    user = await _user(session, auth_user_id)
    if await _my_worker(session, user):
        raise WorkerConflictError("You already have a worker profile")
    worker = await session.scalar(
        select(WorkerProfile)
        .where(WorkerProfile.claim_code_hash == hash_claim_code(code), WorkerProfile.deleted_at.is_(None))
        .with_for_update()
    )
    now = _now()
    if (
        worker is None
        or worker.user_id is not None
        or worker.claim_code_expires_at is None
        or worker.claim_code_expires_at < now
    ):
        raise WorkerConflictError("This code is wrong or has expired. Ask RightConnect for a new one.")
    worker.user_id = user.id
    worker.display_name = user.full_name
    worker.contact_phone = worker.contact_phone or user.phone
    worker.claim_status = "claimed"
    worker.claimed_at = now
    worker.claim_code_hash = None
    worker.claim_code_expires_at = None
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError("You already have a worker profile") from exc
    return await _my_profile_out(session, worker, user)


# ---------- employers: confirm or add work history ----------


async def list_verification_requests(session: AsyncSession, auth_user_id: UUID) -> list[VerificationRequestOut]:
    user = await _user(session, auth_user_id)
    org_ids = await _admin_org_ids(session, user.id)
    if not org_ids:
        return []
    rows = (
        await session.execute(
            select(WorkerExperience, WorkerProfile.display_name, Organization.name, Organization.verification)
            .join(WorkerProfile, WorkerProfile.id == WorkerExperience.worker_id)
            .join(Organization, Organization.id == WorkerExperience.organization_id)
            .where(
                WorkerExperience.status == ExperienceStatus.PENDING.value,
                WorkerExperience.organization_id.in_(org_ids),
                _visible(),
            )
            .order_by(WorkerExperience.created_at)
        )
    ).all()
    return [
        VerificationRequestOut(
            experience=_experience_out(experience, org_name, verification == VerificationStatus.VERIFIED),
            worker_id=experience.worker_id,
            worker_name=worker_name,
            organization_name=org_name,
        )
        for experience, worker_name, org_name, verification in rows
    ]


async def _experience_for_employer(session: AsyncSession, auth_user_id: UUID, experience_id: UUID) -> tuple[User, WorkerExperience]:
    user = await _user(session, auth_user_id)
    experience = await session.get(WorkerExperience, experience_id, with_for_update=True)
    if experience is None or experience.organization_id not in await _admin_org_ids(session, user.id):
        raise WorkerNotFoundError("This confirmation request could not be found")
    if experience.status != ExperienceStatus.PENDING.value:
        raise WorkerConflictError("This request was already answered")
    worker = await session.get(WorkerProfile, experience.worker_id)
    if worker is not None and worker.user_id == user.id:
        raise WorkerAccessError("You can't confirm your own work history")
    return user, experience


async def confirm_experience(session: AsyncSession, auth_user_id: UUID, experience_id: UUID, payload: ExperienceConfirm) -> None:
    user, experience = await _experience_for_employer(session, auth_user_id, experience_id)
    if payload.skills is not None:
        experience.skills = payload.skills
    if payload.role_title:
        experience.role_title = payload.role_title
    experience.status = ExperienceStatus.VERIFIED.value
    experience.verified_by = user.id
    experience.verified_at = _now()
    await session.commit()


async def decline_experience(session: AsyncSession, auth_user_id: UUID, experience_id: UUID) -> None:
    user, experience = await _experience_for_employer(session, auth_user_id, experience_id)
    experience.status = ExperienceStatus.DECLINED.value
    experience.verified_by = user.id
    experience.verified_at = _now()
    await session.commit()


async def employer_add_experience(
    session: AsyncSession, auth_user_id: UUID, worker_id: UUID, payload: EmployerExperienceCreate
) -> None:
    """A company admin certifies that this worker worked for them, with the skills they showed."""
    user = await _user(session, auth_user_id)
    if payload.organization_id not in await _admin_org_ids(session, user.id):
        raise WorkerAccessError("Only an admin of that company can add work history for it")
    worker = await _visible_worker(session, worker_id)
    if worker.user_id == user.id:
        raise WorkerAccessError("You can't verify your own work history")
    if payload.hire_id:
        hire = await session.get(WorkerHire, payload.hire_id)
        if (
            hire is None
            or hire.worker_id != worker.id
            or hire.organization_id != payload.organization_id
            or hire.status not in (HireStatus.ACCEPTED.value, HireStatus.COMPLETED.value)
        ):
            raise WorkerConflictError("That hire doesn't belong to this worker and company")
        already = await session.scalar(select(WorkerExperience.id).where(WorkerExperience.hire_id == hire.id))
        if already is not None:
            raise WorkerConflictError("Work history was already added for this hire")
    organization = await session.get(Organization, payload.organization_id)
    session.add(
        WorkerExperience(
            worker_id=worker.id,
            organization_id=payload.organization_id,
            employer_name=organization.name,
            role_title=payload.role_title,
            start_date=payload.start_date,
            end_date=payload.end_date,
            description=payload.description,
            skills=payload.skills,
            status=ExperienceStatus.VERIFIED.value,
            added_by="employer",
            verified_by=user.id,
            verified_at=_now(),
            hire_id=payload.hire_id,
        )
    )
    await session.commit()


# ---------- hires ----------


async def create_hire(session: AsyncSession, auth_user_id: UUID, worker_id: UUID, payload: HireCreate) -> HireOut:
    user = await _user(session, auth_user_id)
    worker = await _visible_worker(session, worker_id)
    if not reachable(worker):
        raise WorkerConflictError("This worker hasn't joined RightConnect yet, so they can't receive requests.")
    if worker.user_id == user.id:
        raise WorkerConflictError("You can't hire yourself")
    if payload.organization_id and payload.organization_id not in await _admin_org_ids(session, user.id):
        raise WorkerAccessError("You can only hire on behalf of a company you administer")
    pending = await session.scalar(
        select(WorkerHire.id).where(
            WorkerHire.worker_id == worker.id,
            WorkerHire.employer_user_id == user.id,
            WorkerHire.job_id.is_(None),
            WorkerHire.status == HireStatus.PENDING.value,
        )
    )
    if pending is not None:
        raise WorkerConflictError("You already have a request waiting for this worker")
    hire = WorkerHire(
        worker_id=worker.id,
        employer_user_id=user.id,
        organization_id=payload.organization_id,
        initiated_by="employer",
        title=payload.title,
        details=payload.details,
        location=payload.location,
        start_date=payload.start_date,
        pay_offer=payload.pay_offer,
        status=HireStatus.PENDING.value,
    )
    session.add(hire)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError("You already have a request waiting for this worker") from exc
    return await _hire_out(session, hire, user, "employer", await _admin_org_ids(session, user.id))


async def apply_to_job(session: AsyncSession, auth_user_id: UUID, job_id: UUID, payload: JobApply) -> HireOut:
    user, worker = await _require_my_worker(session, auth_user_id)
    if worker.blocked_at is not None:
        raise WorkerAccessError("Your worker profile is suspended. Contact RightConnect support.")
    job = await session.get(JobPost, job_id)
    if job is None or job.status != "open":
        raise WorkerNotFoundError("This job is closed or no longer exists")
    if job.poster_user_id == user.id:
        raise WorkerConflictError("You can't apply to your own job")
    existing = await session.scalar(
        select(WorkerHire.id).where(
            WorkerHire.worker_id == worker.id,
            WorkerHire.job_id == job.id,
            WorkerHire.status.in_([HireStatus.PENDING.value, HireStatus.ACCEPTED.value]),
        )
    )
    if existing is not None:
        raise WorkerConflictError("You already applied to this job")
    hire = WorkerHire(
        worker_id=worker.id,
        employer_user_id=job.poster_user_id,
        organization_id=job.organization_id,
        job_id=job.id,
        initiated_by="worker",
        title=job.title,
        details=payload.message,
        location=", ".join(part for part in (job.area, job.city) if part),
        start_date=job.starts_on,
        pay_offer=job.pay,
        status=HireStatus.PENDING.value,
    )
    session.add(hire)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError("You already applied to this job") from exc
    return await _hire_out(session, hire, user, "worker", set())


async def _hire_out(session: AsyncSession, hire: WorkerHire, me: User | None, side: str, my_org_ids: set[UUID]) -> HireOut:
    worker = await session.get(WorkerProfile, hire.worker_id)
    employer = await session.get(User, hire.employer_user_id)
    organization = await session.get(Organization, hire.organization_id) if hire.organization_id else None
    worker_user = await session.get(User, worker.user_id) if worker and worker.user_id else None
    shared = hire.status in (HireStatus.ACCEPTED.value, HireStatus.COMPLETED.value)
    contact = None
    if shared and side == "worker" and employer is not None:
        contact = Contact(name=organization.name if organization else employer.full_name, phone=employer.phone, email=employer.email)
    elif shared and side == "employer" and worker is not None:
        contact = Contact(
            name=worker.display_name,
            phone=worker.contact_phone or (worker_user.phone if worker_user else None),
            email=worker_user.email if worker_user else None,
        )
    reviewed = (await session.scalar(select(WorkerReview.id).where(WorkerReview.hire_id == hire.id))) is not None
    has_history = (await session.scalar(select(WorkerExperience.id).where(WorkerExperience.hire_id == hire.id))) is not None
    return HireOut(
        id=hire.id,
        worker_id=hire.worker_id,
        worker_name=worker.display_name if worker else "Worker",
        worker_headline=worker.headline if worker else "",
        employer_name=employer.full_name if employer else "Employer",
        organization_id=hire.organization_id,
        organization_name=organization.name if organization else None,
        job_id=hire.job_id,
        initiated_by=hire.initiated_by,
        title=hire.title,
        details=hire.details,
        location=hire.location,
        start_date=hire.start_date,
        pay_offer=hire.pay_offer,
        status=hire.status,
        created_at=hire.created_at,
        responded_at=hire.responded_at,
        completed_at=hire.completed_at,
        my_side=side,
        counterpart_contact=contact,
        can_review=side == "employer" and hire.status == HireStatus.COMPLETED.value and not reviewed and me is not None and hire.employer_user_id == me.id,
        reviewed=reviewed,
        can_add_experience=(
            side == "employer"
            and hire.organization_id is not None
            and hire.organization_id in my_org_ids
            and hire.status in (HireStatus.ACCEPTED.value, HireStatus.COMPLETED.value)
            and not has_history
        ),
    )


async def list_hires(session: AsyncSession, auth_user_id: UUID) -> HiresResponse:
    user = await _user(session, auth_user_id)
    worker = await _my_worker(session, user)
    org_ids = await _admin_org_ids(session, user.id)
    as_worker = (
        (await session.scalars(select(WorkerHire).where(WorkerHire.worker_id == worker.id).order_by(WorkerHire.created_at.desc()).limit(100))).all()
        if worker
        else []
    )
    employer_filter = WorkerHire.employer_user_id == user.id
    if org_ids:
        employer_filter = or_(employer_filter, WorkerHire.organization_id.in_(org_ids))
    as_employer = (
        await session.scalars(select(WorkerHire).where(employer_filter).order_by(WorkerHire.created_at.desc()).limit(100))
    ).all()
    return HiresResponse(
        as_worker=[await _hire_out(session, hire, user, "worker", org_ids) for hire in as_worker],
        as_employer=[await _hire_out(session, hire, user, "employer", org_ids) for hire in as_employer],
    )


async def hire_action(session: AsyncSession, auth_user_id: UUID, hire_id: UUID, action: str) -> HireOut:
    user = await _user(session, auth_user_id)
    hire = await session.get(WorkerHire, hire_id, with_for_update=True)
    if hire is None:
        raise WorkerNotFoundError("This hire could not be found")
    worker = await _my_worker(session, user)
    org_ids = await _admin_org_ids(session, user.id)
    if worker is not None and hire.worker_id == worker.id:
        side = "worker"
    elif hire.employer_user_id == user.id or (hire.organization_id is not None and hire.organization_id in org_ids):
        side = "employer"
    else:
        raise WorkerNotFoundError("This hire could not be found")
    apply_hire_action(hire, side, action)
    await session.commit()
    return await _hire_out(session, hire, user, side, org_ids)


def apply_hire_action(hire: WorkerHire, side: str, action: str) -> None:
    if not hire_action_allowed(hire.status, hire.initiated_by, side, action):
        raise WorkerConflictError("This request can't be changed that way any more")
    now = _now()
    hire.status = {
        "accept": HireStatus.ACCEPTED.value,
        "decline": HireStatus.DECLINED.value,
        "cancel": HireStatus.CANCELLED.value,
        "complete": HireStatus.COMPLETED.value,
    }[action]
    if action in ("accept", "decline"):
        hire.responded_at = now
    if action == "complete":
        hire.completed_at = now


async def review_hire(session: AsyncSession, auth_user_id: UUID, hire_id: UUID, payload: ReviewCreate) -> HireOut:
    user = await _user(session, auth_user_id)
    hire = await session.get(WorkerHire, hire_id, with_for_update=True)
    if hire is None or hire.employer_user_id != user.id:
        raise WorkerNotFoundError("This hire could not be found")
    if hire.status != HireStatus.COMPLETED.value:
        raise WorkerConflictError("Mark the work as completed before leaving a review")
    if await session.scalar(select(WorkerReview.id).where(WorkerReview.hire_id == hire.id)) is not None:
        raise WorkerConflictError("You already reviewed this hire")
    session.add(WorkerReview(hire_id=hire.id, worker_id=hire.worker_id, reviewer_id=user.id, rating=payload.rating, body=payload.body))
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError("You already reviewed this hire") from exc
    average, count = (
        await session.execute(
            select(func.avg(WorkerReview.rating), func.count(WorkerReview.id)).where(WorkerReview.worker_id == hire.worker_id)
        )
    ).one()
    worker = await session.get(WorkerProfile, hire.worker_id, with_for_update=True)
    worker.average_rating = round(float(average or 0), 1)
    worker.review_count = count or 0
    await session.commit()
    return await _hire_out(session, hire, user, "employer", await _admin_org_ids(session, user.id))


# ---------- job posts ----------


async def search_companies(session: AsyncSession, query: str) -> list[dict]:
    """Companies a worker can name as a past employer (claimed or not), so the company can confirm the job."""
    rows = (
        await session.execute(
            select(Organization.id, Organization.name, Organization.city, Organization.verification)
            .where(Organization.deleted_at.is_(None), Organization.name.ilike(_like(query), escape="\\"))
            .order_by(Organization.name)
            .limit(10)
        )
    ).all()
    return [
        {"organization_id": org_id, "name": name, "city": city, "verified": verification == VerificationStatus.VERIFIED}
        for org_id, name, city, verification in rows
    ]


async def _job_out(session: AsyncSession, job: JobPost, mine: bool) -> JobOut:
    poster = await session.get(User, job.poster_user_id)
    organization = await session.get(Organization, job.organization_id) if job.organization_id else None
    count = None
    if mine:
        count = (await session.scalar(select(func.count(WorkerHire.id)).where(WorkerHire.job_id == job.id))) or 0
    return JobOut(
        id=job.id,
        title=job.title,
        skill=job.skill,
        city=job.city,
        area=job.area,
        pincode=job.pincode,
        openings=job.openings,
        pay=job.pay,
        starts_on=job.starts_on,
        description=job.description,
        status=job.status,
        poster_name=organization.name if organization else (poster.full_name if poster else "Employer"),
        organization_name=organization.name if organization else None,
        organization_verified=bool(organization and organization.verification == VerificationStatus.VERIFIED),
        created_at=job.created_at,
        mine=mine,
        applied=False,
        contact_available=bool(job.show_contact and job.contact_phone and job.status == "open"),
        application_count=count,
    )


async def list_open_jobs(
    session: AsyncSession,
    query: str | None,
    city: str | None,
    page: int,
    page_size: int,
    near_pincode: str | None = None,
    near_city: str | None = None,
) -> list[JobOut]:
    stmt = (
        select(JobPost)
        .join(User, User.id == JobPost.poster_user_id)
        .where(JobPost.status == "open", User.deleted_at.is_(None), User.blocked_at.is_(None))
    )
    if query:
        words, services = search_terms(query)
        conditions = [
            column.ilike(_like(word), escape="\\")
            for word in [*words, *services]
            for column in (JobPost.title, JobPost.skill, JobPost.description)
        ]
        if conditions:
            stmt = stmt.where(or_(*conditions))
    if city:
        stmt = stmt.where(JobPost.city.ilike(_like(city), escape="\\"))
    ordering = [JobPost.created_at.desc()]
    nearness = proximity_rank(JobPost.pincode, JobPost.city, near_pincode, near_city)
    if nearness is not None:
        ordering.insert(0, nearness.desc())
    jobs = (await session.scalars(stmt.order_by(*ordering).offset((page - 1) * page_size).limit(page_size))).all()
    results = [await _job_out(session, job, mine=False) for job in jobs]
    if nearness is not None:
        for job, out in zip(jobs, results):
            out.nearness = proximity(job.pincode, job.city, near_pincode, near_city)
    return results


async def job_contact(session: AsyncSession, auth_user_id: UUID, job_id: UUID) -> DirectContact:
    """The poster's call/WhatsApp number for an open job, for signed-in users, when the poster allows it."""
    await _user(session, auth_user_id)
    job = await session.get(JobPost, job_id)
    if job is None or job.status != "open":
        raise WorkerNotFoundError("This job is closed or no longer exists")
    if not job.show_contact or not job.contact_phone:
        raise WorkerAccessError("The employer hasn't shared a number for this job. Apply and they'll contact you.")
    poster = await session.get(User, job.poster_user_id)
    organization = await session.get(Organization, job.organization_id) if job.organization_id else None
    name = organization.name if organization else (poster.full_name if poster else "Employer")
    return DirectContact(name=name, phone=job.contact_phone)


async def list_my_jobs(session: AsyncSession, auth_user_id: UUID) -> list[JobOut]:
    user = await _user(session, auth_user_id)
    jobs = (
        await session.scalars(select(JobPost).where(JobPost.poster_user_id == user.id).order_by(JobPost.created_at.desc()).limit(100))
    ).all()
    return [await _job_out(session, job, mine=True) for job in jobs]


async def create_job(session: AsyncSession, auth_user_id: UUID, payload: JobCreate) -> JobOut:
    user = await _user(session, auth_user_id)
    if payload.organization_id and payload.organization_id not in await _admin_org_ids(session, user.id):
        raise WorkerAccessError("You can only post jobs for a company you administer")
    job = JobPost(
        poster_user_id=user.id,
        organization_id=payload.organization_id,
        title=payload.title,
        skill=payload.skill,
        city=payload.city,
        area=payload.area,
        pincode=payload.pincode,
        openings=payload.openings,
        pay=payload.pay,
        starts_on=payload.starts_on,
        description=payload.description,
        contact_phone=payload.contact_phone or user.phone,
        show_contact=payload.show_contact,
        status="open",
    )
    session.add(job)
    await session.commit()
    return await _job_out(session, job, mine=True)


async def close_job(session: AsyncSession, auth_user_id: UUID, job_id: UUID) -> JobOut:
    user = await _user(session, auth_user_id)
    job = await session.get(JobPost, job_id)
    if job is None or job.poster_user_id != user.id:
        raise WorkerNotFoundError("This job could not be found")
    job.status = "closed"
    job.closed_at = _now()
    await session.commit()
    return await _job_out(session, job, mine=True)


# ---------- personal worker links (no Google/email needed) ----------

LINK_INVALID = "This link no longer works. Ask RightConnect to send you a new one."


async def _link_worker(session: AsyncSession, key: str, *, lock: bool = False) -> WorkerProfile:
    stmt = select(WorkerProfile).where(WorkerProfile.access_key_hash == hash_link_key(key), WorkerProfile.deleted_at.is_(None))
    worker = await session.scalar(stmt.with_for_update() if lock else stmt)
    if worker is None:
        raise WorkerAccessError(LINK_INVALID)
    if worker.blocked_at is not None:
        raise WorkerAccessError("This profile is suspended. Contact RightConnect support.")
    if worker.user_id is not None:
        owner = await session.get(User, worker.user_id)
        if owner is None or owner.deleted_at is not None:
            raise WorkerAccessError(LINK_INVALID)
        if owner.blocked_at is not None:
            raise WorkerAccessError("This profile is suspended. Contact RightConnect support.")
    return worker


async def _link_profile_out(session: AsyncSession, worker: WorkerProfile) -> LinkProfile:
    hires = (
        await session.scalars(
            select(WorkerHire).where(WorkerHire.worker_id == worker.id).order_by(WorkerHire.created_at.desc()).limit(50)
        )
    ).all()
    availability = effective_availability(worker.availability, worker.busy_until, date.today())
    return LinkProfile(
        display_name=worker.display_name,
        headline=worker.headline,
        city=worker.city,
        area=worker.area,
        availability=availability,
        busy_until=worker.busy_until if availability == Availability.BUSY.value else None,
        connected=worker.user_id is not None,
        hires=[await _hire_out(session, hire, None, "worker", set()) for hire in hires],
        contact_views=await _contact_views(session, worker.id),
    )


async def link_report_contact_view(session: AsyncSession, key: str, view_id: UUID, reason: str) -> LinkProfile:
    worker = await _link_worker(session, key)
    await _report_view(session, worker, view_id, reason)
    return await _link_profile_out(session, worker)


async def link_profile(session: AsyncSession, key: str) -> LinkProfile:
    return await _link_profile_out(session, await _link_worker(session, key))


async def link_set_availability(session: AsyncSession, key: str, payload: AvailabilityUpdate) -> LinkProfile:
    worker = await _link_worker(session, key)
    if payload.availability == Availability.BUSY.value and payload.busy_until and payload.busy_until < date.today():
        raise WorkerConflictError("The 'busy until' date has already passed")
    worker.availability = payload.availability
    worker.busy_until = payload.busy_until
    worker.availability_updated_at = _now()
    await session.commit()
    return await _link_profile_out(session, worker)


async def link_hire_action(session: AsyncSession, key: str, hire_id: UUID, action: str) -> LinkProfile:
    worker = await _link_worker(session, key)
    hire = await session.get(WorkerHire, hire_id, with_for_update=True)
    if hire is None or hire.worker_id != worker.id:
        raise WorkerNotFoundError("This request could not be found")
    apply_hire_action(hire, "worker", action)
    await session.commit()
    return await _link_profile_out(session, worker)


def attach_worker(worker: WorkerProfile, user: User) -> None:
    """Give an admin-made profile to a signed-in account; the link keeps working too."""
    worker.user_id = user.id
    worker.contact_phone = worker.contact_phone or user.phone
    worker.claim_status = "claimed"
    worker.claimed_at = _now()
    worker.claim_code_hash = None
    worker.claim_code_expires_at = None


async def worker_for_link_key(session: AsyncSession, key: str | None) -> WorkerProfile | None:
    """The unattached profile a link key opens, used at sign-up so no second worker profile is made."""
    if not key:
        return None
    return await session.scalar(
        select(WorkerProfile)
        .where(
            WorkerProfile.access_key_hash == hash_link_key(key),
            WorkerProfile.deleted_at.is_(None),
            WorkerProfile.blocked_at.is_(None),
            WorkerProfile.user_id.is_(None),
        )
        .with_for_update()
    )


async def link_connect_account(session: AsyncSession, auth_user_id: UUID, key: str) -> MyWorkerProfile:
    """Attach the link's profile to the signed-in account instead of creating a second profile."""
    user = await _user(session, auth_user_id)
    worker = await _link_worker(session, key, lock=True)
    if worker.user_id == user.id:
        return await _my_profile_out(session, worker, user)
    if worker.user_id is not None:
        raise WorkerConflictError("This profile is already connected to another account.")
    if await _my_worker(session, user):
        raise WorkerConflictError(
            "This account already has its own worker profile. Ask RightConnect to remove the extra one."
        )
    attach_worker(worker, user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError("This account already has its own worker profile.") from exc
    return await _my_profile_out(session, worker, user)


# ---------- platform admin ----------


def _admin_log(session: AsyncSession, admin: User, action: str, worker: WorkerProfile, reason: str | None = None) -> None:
    session.add(
        AdminAction(
            admin_user_id=admin.id, action=action, target_type="worker", target_id=worker.id,
            target_label=worker.display_name, reason=reason,
        )
    )


def _issue_claim_code(worker: WorkerProfile) -> str:
    code = generate_claim_code()
    worker.claim_code_hash = hash_claim_code(code)
    worker.claim_code_expires_at = _now() + timedelta(days=CLAIM_CODE_DAYS)
    return code


async def admin_create_worker(session: AsyncSession, admin: User, payload: AdminWorkerCreate) -> ClaimCodeOut:
    worker = WorkerProfile(
        display_name=payload.full_name,
        contact_phone=payload.contact_phone,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        availability=Availability.AVAILABLE.value,
        availability_updated_at=_now(),
        claim_status="unclaimed",
        adult_confirmed_at=_now(),
        created_by=admin.id,
    )
    _apply_fields(worker, payload)
    code = _issue_claim_code(worker)
    session.add(worker)
    await session.flush()
    _admin_log(session, admin, "create_worker", worker)
    await session.commit()
    return ClaimCodeOut(worker_id=worker.id, display_name=worker.display_name, claim_code=code, expires_at=worker.claim_code_expires_at)


async def _admin_worker(session: AsyncSession, worker_id: UUID) -> WorkerProfile:
    worker = await session.get(WorkerProfile, worker_id, with_for_update=True)
    if worker is None:
        raise WorkerNotFoundError("Worker not found")
    return worker


async def admin_new_claim_code(session: AsyncSession, admin: User, worker_id: UUID) -> ClaimCodeOut:
    worker = await _admin_worker(session, worker_id)
    if worker.user_id is not None or worker.deleted_at is not None:
        raise WorkerConflictError("This worker profile is already claimed")
    code = _issue_claim_code(worker)
    _admin_log(session, admin, "worker_claim_code", worker)
    await session.commit()
    return ClaimCodeOut(worker_id=worker.id, display_name=worker.display_name, claim_code=code, expires_at=worker.claim_code_expires_at)


async def admin_worker_link(session: AsyncSession, admin: User, worker_id: UUID) -> WorkerLinkOut:
    """Create (or reset) the worker's personal link; any earlier link stops working."""
    worker = await _admin_worker(session, worker_id)
    if worker.deleted_at is not None:
        raise WorkerConflictError("Restore this worker before sending a link")
    key = generate_link_key()
    worker.access_key_hash = hash_link_key(key)
    worker.access_key_created_at = _now()
    _admin_log(session, admin, "worker_link", worker)
    await session.commit()
    owner = await session.get(User, worker.user_id) if worker.user_id else None
    return WorkerLinkOut(
        worker_id=worker.id, display_name=worker.display_name, key=key,
        contact_phone=worker.contact_phone or (owner.phone if owner else None),
    )


async def admin_revoke_worker_link(session: AsyncSession, admin: User, worker_id: UUID) -> None:
    worker = await _admin_worker(session, worker_id)
    worker.access_key_hash = None
    worker.access_key_created_at = None
    _admin_log(session, admin, "worker_link_off", worker)
    await session.commit()


async def admin_list_workers(session: AsyncSession, status: str, q: str | None) -> list[AdminWorkerOut]:
    stmt = select(WorkerProfile, User.email).outerjoin(User, User.id == WorkerProfile.user_id)
    live = (WorkerProfile.deleted_at.is_(None),)
    shared_phone = (
        select(WorkerProfile.contact_phone)
        .where(WorkerProfile.contact_phone.is_not(None), WorkerProfile.deleted_at.is_(None))
        .group_by(WorkerProfile.contact_phone)
        .having(func.count(WorkerProfile.id) > 1)
    )
    if status == "unclaimed":
        stmt = stmt.where(*live, WorkerProfile.user_id.is_(None))
    elif status == "claimed":
        stmt = stmt.where(*live, WorkerProfile.user_id.is_not(None))
    elif status == "duplicates":
        stmt = stmt.where(*live, WorkerProfile.contact_phone.in_(shared_phone))
    elif status == "blocked":
        stmt = stmt.where(*live, WorkerProfile.blocked_at.is_not(None))
    elif status == "deleted":
        stmt = stmt.where(WorkerProfile.deleted_at.is_not(None))
    if q:
        pattern = _like(q)
        stmt = stmt.where(
            or_(
                WorkerProfile.display_name.ilike(pattern, escape="\\"),
                WorkerProfile.headline.ilike(pattern, escape="\\"),
                WorkerProfile.contact_phone.ilike(pattern, escape="\\"),
                WorkerProfile.contact_email.ilike(pattern, escape="\\"),
                User.email.ilike(pattern, escape="\\"),
            )
        )
    order = [WorkerProfile.contact_phone, WorkerProfile.created_at.desc()] if status == "duplicates" else [WorkerProfile.created_at.desc()]
    rows = (await session.execute(stmt.order_by(*order).limit(200))).all()
    phones = {worker.contact_phone for worker, _ in rows if worker.contact_phone}
    shared_phones: set[str] = set()
    # phone -> the worker's own account profiles using it, which an admin-made profile can be merged into
    account_profiles: dict[str, list[tuple[UUID, str]]] = {}
    if phones:
        shared_phones = set((await session.scalars(shared_phone.where(WorkerProfile.contact_phone.in_(phones)))).all())
    if shared_phones:
        for phone, worker_id, email in (
            await session.execute(
                select(WorkerProfile.contact_phone, WorkerProfile.id, User.email)
                .join(User, User.id == WorkerProfile.user_id)
                .where(WorkerProfile.contact_phone.in_(shared_phones), WorkerProfile.deleted_at.is_(None))
            )
        ).all():
            account_profiles.setdefault(phone, []).append((worker_id, email))

    def merge_target(worker: WorkerProfile) -> tuple[UUID, str] | None:
        if worker.user_id is not None or worker.deleted_at is not None:
            return None
        targets = account_profiles.get(worker.contact_phone or "", [])
        return targets[0] if len(targets) == 1 else None

    results = []
    for worker, email in rows:
        target = merge_target(worker)
        results.append(
            AdminWorkerOut(
                id=worker.id,
                display_name=worker.display_name,
                headline=worker.headline,
                city=worker.city,
                area=worker.area,
                pincode=worker.pincode,
                claim_status="claimed" if worker.user_id else "unclaimed",
                contact_phone=worker.contact_phone,
                contact_email=worker.contact_email,
                owner_email=email,
                availability=worker.availability,
                review_count=worker.review_count,
                blocked_at=worker.blocked_at,
                blocked_reason=worker.blocked_reason,
                deleted_at=worker.deleted_at,
                created_at=worker.created_at,
                has_link=worker.access_key_hash is not None,
                possible_duplicate=worker.deleted_at is None and worker.contact_phone in shared_phones,
                merge_into_id=target[0] if target else None,
                merge_into_email=target[1] if target else None,
            )
        )
    return results


async def admin_merge_worker(session: AsyncSession, admin: User, worker_id: UUID, into_worker_id: UUID) -> None:
    """Move an admin-made profile (jobs, reviews, work history, link, contact log) into the worker's own account
    profile, then delete the empty copy. Only when both use the same phone, which RightConnect collected."""
    if worker_id == into_worker_id:
        raise WorkerConflictError("Choose two different profiles")
    source = await _admin_worker(session, worker_id)
    target = await _admin_worker(session, into_worker_id)
    if source.deleted_at is not None or target.deleted_at is not None:
        raise WorkerConflictError("Restore both profiles before merging")
    if source.user_id is not None:
        raise WorkerConflictError("Only a profile RightConnect added (not connected to an account) can be merged")
    if target.user_id is None:
        raise WorkerConflictError("Merge into the worker's own account profile")
    owner = await session.get(User, target.user_id)
    target_phone = target.contact_phone or (owner.phone if owner else None)
    if not source.contact_phone or source.contact_phone != target_phone:
        raise WorkerConflictError("The phone numbers don't match. Check with the worker before merging.")
    try:
        await _merge_rows(session, admin, source, target)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkerConflictError(
            "Both profiles have an open request from the same employer or job. Finish or cancel one, then merge."
        ) from exc


async def _merge_rows(session: AsyncSession, admin: User, source: WorkerProfile, target: WorkerProfile) -> None:
    for model in (WorkerHire, WorkerExperience, WorkerReview):
        await session.execute(update(model).where(model.worker_id == source.id).values(worker_id=target.id))
    already_viewed = select(WorkerContactView.viewer_user_id).where(WorkerContactView.worker_id == target.id)
    # Someone who viewed both profiles: fold the old row into the account's row so reports and counts survive.
    old = aliased(WorkerContactView)
    await session.execute(
        update(WorkerContactView)
        .where(
            WorkerContactView.worker_id == target.id,
            old.worker_id == source.id,
            old.viewer_user_id == WorkerContactView.viewer_user_id,
        )
        .values(
            view_count=WorkerContactView.view_count + old.view_count,
            first_viewed_at=func.least(WorkerContactView.first_viewed_at, old.first_viewed_at),
            last_viewed_at=func.greatest(WorkerContactView.last_viewed_at, old.last_viewed_at),
            reported_at=func.coalesce(WorkerContactView.reported_at, old.reported_at),
            report_reason=func.coalesce(WorkerContactView.report_reason, old.report_reason),
        )
        .execution_options(synchronize_session=False)
    )
    await session.execute(
        delete(WorkerContactView).where(WorkerContactView.worker_id == source.id, WorkerContactView.viewer_user_id.in_(already_viewed))
    )
    await session.execute(update(WorkerContactView).where(WorkerContactView.worker_id == source.id).values(worker_id=target.id))
    merge_profile_fields(target, source)
    link_hash, link_created = source.access_key_hash, source.access_key_created_at
    source.access_key_hash = source.access_key_created_at = None
    source.claim_code_hash = source.claim_code_expires_at = None
    source.review_count, source.average_rating = 0, 0
    source.deleted_at = _now()
    if link_hash and not target.access_key_hash:
        # The worker keeps using the link they were sent; clear it on the old row first (unique index).
        await session.flush()
        target.access_key_hash, target.access_key_created_at = link_hash, link_created
    _admin_log(session, admin, "merge_worker", source, f"Merged into {target.display_name} ({target.id})")


async def admin_contact_reports(session: AsyncSession) -> list[AdminContactReportOut]:
    """Callers that workers reported, newest first."""
    rows = (
        await session.execute(
            select(WorkerContactView, WorkerProfile.display_name, User)
            .join(WorkerProfile, WorkerProfile.id == WorkerContactView.worker_id)
            .join(User, User.id == WorkerContactView.viewer_user_id)
            .where(WorkerContactView.reported_at.is_not(None))
            .order_by(WorkerContactView.reported_at.desc())
            .limit(200)
        )
    ).all()
    counts = dict(
        (
            await session.execute(
                select(WorkerContactView.viewer_user_id, func.count())
                .where(WorkerContactView.reported_at.is_not(None))
                .group_by(WorkerContactView.viewer_user_id)
            )
        ).all()
    )
    return [
        AdminContactReportOut(
            id=view.id, worker_id=view.worker_id, worker_name=worker_name,
            viewer_user_id=viewer.id, viewer_name=viewer.full_name, viewer_email=viewer.email,
            viewer_blocked=viewer.blocked_at is not None, view_count=view.view_count,
            first_viewed_at=view.first_viewed_at, reported_at=view.reported_at, report_reason=view.report_reason,
            report_count=counts.get(viewer.id, 1),
        )
        for view, worker_name, viewer in rows
    ]


async def admin_dismiss_contact_report(session: AsyncSession, admin: User, view_id: UUID) -> None:
    view = await session.get(WorkerContactView, view_id, with_for_update=True)
    if view is None or view.reported_at is None:
        raise WorkerNotFoundError("Report not found")
    worker = await session.get(WorkerProfile, view.worker_id)
    view.reported_at = view.report_reason = None
    if worker is not None:
        _admin_log(session, admin, "dismiss_contact_report", worker)
    await session.commit()


async def admin_moderate_worker(session: AsyncSession, admin: User, worker_id: UUID, action: str, reason: str | None) -> None:
    worker = await _admin_worker(session, worker_id)
    now = _now()
    if action == "block":
        worker.blocked_at, worker.blocked_reason = now, reason
    elif action == "unblock":
        worker.blocked_at, worker.blocked_reason = None, None
    elif action == "delete":
        worker.deleted_at = now
        worker.claim_code_hash = None
    elif action == "restore":
        if worker.user_id is not None:
            active = await session.scalar(
                select(WorkerProfile.id).where(
                    WorkerProfile.user_id == worker.user_id, WorkerProfile.deleted_at.is_(None), WorkerProfile.id != worker.id
                )
            )
            if active is not None:
                raise WorkerConflictError("This person already created a new worker profile")
        worker.deleted_at = None
    _admin_log(session, admin, f"{action}_worker", worker, reason)
    await session.commit()
