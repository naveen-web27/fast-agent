"""Local workforce hub: worker profiles, employer-verified skills, hires, reviews, job posts and admin-added workers.

Trust model: a worker's own skills are shown as self-declared. A skill becomes employer-verified only when an
admin of a RightConnect-verified company confirms (or adds) a job in the worker's history that lists it.
"""
import hashlib
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import and_, case, exists, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.location import proximity, proximity_rank
from app.features.marketplace.catalog import search_terms
from app.features.workers.schemas import (
    AdminWorkerCreate,
    AdminWorkerOut,
    AvailabilityUpdate,
    ClaimCodeOut,
    Contact,
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
    LocationUpdate,
    MyWorkerProfile,
    ReviewCreate,
    SkillOut,
    VerificationRequestOut,
    WorkerCreate,
    WorkerDetail,
    WorkerListResponse,
    WorkerReviewOut,
    WorkerSummary,
    WorkerUpdate,
)
from app.models.admin_action import AdminAction
from app.models.organization_member import MemberRole, OrganizationMember
from app.models.profile import Organization, VerificationStatus
from app.models.user import User, active_user_by_auth_id
from app.models.worker import (
    Availability,
    ExperienceStatus,
    HireStatus,
    JobPost,
    WorkerExperience,
    WorkerHire,
    WorkerProfile,
    WorkerReview,
)

STALE_AFTER_DAYS = 14
CLAIM_CODE_DAYS = 30
CLAIM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


class WorkerNotFoundError(Exception):
    """The worker, job, hire or experience doesn't exist or isn't visible to the caller."""


class WorkerAccessError(Exception):
    """The caller isn't allowed to do this (not the worker, not the employer, not a company admin)."""


class WorkerConflictError(Exception):
    """Duplicate profile/request, wrong state for this action, or a claim that can't be used."""


class WorkerIdentityError(Exception):
    """The caller hasn't finished creating their RightConnect account."""


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


# ---------- shared lookups ----------


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
        contact_available=worker.user_id is not None and bool(worker.show_contact),
        availability=availability,
        busy_until=worker.busy_until if availability == Availability.BUSY.value else None,
        availability_stale=availability_is_stale(availability, worker.availability_updated_at, _now()),
        avatar_url=worker.avatar_url,
        average_rating=float(worker.average_rating or 0),
        review_count=worker.review_count,
        verified_skill_count=sum(1 for skill in skills if skill.verified),
        skills=skills,
        claimed=worker.user_id is not None,
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


async def worker_contact(session: AsyncSession, auth_user_id: UUID, worker_id: UUID) -> DirectContact:
    """The worker's call/WhatsApp number, for signed-in users, only when the worker allows direct contact."""
    await _user(session, auth_user_id)
    worker = await _visible_worker(session, worker_id)
    if worker.user_id is None or not worker.show_contact:
        raise WorkerAccessError("This worker shares their number after you send a hire request and they accept.")
    owner = await session.get(User, worker.user_id)
    phone = worker.contact_phone or (owner.phone if owner else None)
    if not phone:
        raise WorkerNotFoundError("This worker hasn't added a phone number yet. Send a hire request instead.")
    return DirectContact(name=worker.display_name, phone=phone)


async def get_worker(session: AsyncSession, worker_id: UUID) -> WorkerDetail:
    worker = await _visible_worker(session, worker_id)
    return WorkerDetail(**await _detail_fields(session, worker, include_private=False))


# ---------- the worker's own profile ----------


async def _my_profile_out(session: AsyncSession, worker: WorkerProfile, user: User) -> MyWorkerProfile:
    return MyWorkerProfile(
        **await _detail_fields(session, worker, include_private=True),
        contact_phone=worker.contact_phone or user.phone,
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
    if worker.user_id is None:
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


async def _hire_out(session: AsyncSession, hire: WorkerHire, me: User, side: str, my_org_ids: set[UUID]) -> HireOut:
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
        can_review=side == "employer" and hire.status == HireStatus.COMPLETED.value and not reviewed and hire.employer_user_id == me.id,
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
    await session.commit()
    return await _hire_out(session, hire, user, side, org_ids)


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


async def admin_list_workers(session: AsyncSession, status: str, q: str | None) -> list[AdminWorkerOut]:
    stmt = select(WorkerProfile, User.email).outerjoin(User, User.id == WorkerProfile.user_id)
    live = (WorkerProfile.deleted_at.is_(None),)
    if status == "unclaimed":
        stmt = stmt.where(*live, WorkerProfile.user_id.is_(None))
    elif status == "claimed":
        stmt = stmt.where(*live, WorkerProfile.user_id.is_not(None))
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
                User.email.ilike(pattern, escape="\\"),
            )
        )
    rows = (await session.execute(stmt.order_by(WorkerProfile.created_at.desc()).limit(200))).all()
    return [
        AdminWorkerOut(
            id=worker.id,
            display_name=worker.display_name,
            headline=worker.headline,
            city=worker.city,
            area=worker.area,
            pincode=worker.pincode,
            claim_status="claimed" if worker.user_id else "unclaimed",
            contact_phone=worker.contact_phone,
            owner_email=email,
            availability=worker.availability,
            review_count=worker.review_count,
            blocked_at=worker.blocked_at,
            blocked_reason=worker.blocked_reason,
            deleted_at=worker.deleted_at,
            created_at=worker.created_at,
        )
        for worker, email in rows
    ]


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
