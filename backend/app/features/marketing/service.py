"""RightConnect Marketing lead management: client enquiries, follow-up history, payments and feedback."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.marketing.rules import payment_state, status_after_activity, status_change_text
from app.features.marketing.schemas import ActivityCreate, ActivityOut, ActivityResult, LeadCreate, LeadOut, LeadUpdate
from app.models.marketing_lead import MarketingLead, MarketingLeadActivity
from app.models.user import User

# Fields that can't be cleared, so a null in an update is ignored.
REQUIRED = ("phone", "status")


class LeadNotFoundError(Exception):
    """The lead or activity doesn't exist."""


class LeadConflictError(Exception):
    """Another lead already uses this phone number."""


async def _totals(session: AsyncSession, lead_ids: list[UUID]) -> dict[UUID, tuple[int, datetime | None]]:
    """lead id -> (money received, time of the latest activity)."""
    if not lead_ids:
        return {}
    rows = await session.execute(
        select(
            MarketingLeadActivity.lead_id,
            func.coalesce(func.sum(case((MarketingLeadActivity.kind == "payment", MarketingLeadActivity.amount), else_=0)), 0),
            func.max(MarketingLeadActivity.created_at),
        )
        .where(MarketingLeadActivity.lead_id.in_(lead_ids))
        .group_by(MarketingLeadActivity.lead_id)
    )
    return {lead_id: (int(paid), last) for lead_id, paid, last in rows.all()}


def _out(lead: MarketingLead, totals: dict[UUID, tuple[int, datetime | None]]) -> LeadOut:
    paid, last = totals.get(lead.id, (0, None))
    return LeadOut(
        id=lead.id, full_name=lead.full_name, phone=lead.phone, business_name=lead.business_name,
        business_type=lead.business_type, city=lead.city, service=lead.service, source=lead.source,
        status=lead.status, deal_amount=lead.deal_amount, paid_amount=paid, payment=payment_state(lead.deal_amount, paid),
        follow_up_on=lead.follow_up_on, next_action=lead.next_action, rating=lead.rating, feedback=lead.feedback,
        notes=lead.notes, last_activity_at=last, created_at=lead.created_at, updated_at=lead.updated_at,
    )


async def _one_out(session: AsyncSession, lead: MarketingLead) -> LeadOut:
    await session.refresh(lead)
    return _out(lead, await _totals(session, [lead.id]))


async def _get(session: AsyncSession, lead_id: UUID) -> MarketingLead:
    lead = await session.get(MarketingLead, lead_id)
    if lead is None:
        raise LeadNotFoundError("Lead not found")
    return lead


def _set_status(session: AsyncSession, lead: MarketingLead, status: str, admin: User) -> None:
    """Change the status and record the change in the lead's history."""
    if status == lead.status:
        return
    session.add(MarketingLeadActivity(
        lead_id=lead.id, kind="status", text=status_change_text(lead.status, status), created_by=admin.id,
        created_at=datetime.now(timezone.utc),
    ))
    lead.status = status


async def list_leads(session: AsyncSession) -> list[LeadOut]:
    """Newest first; the page filters, groups and searches them."""
    leads = (await session.scalars(select(MarketingLead).order_by(MarketingLead.created_at.desc()).limit(5000))).all()
    totals = await _totals(session, [lead.id for lead in leads])
    return [_out(lead, totals) for lead in leads]


async def create_lead(session: AsyncSession, admin: User, payload: LeadCreate) -> LeadOut:
    existing = await session.scalar(select(MarketingLead).where(MarketingLead.phone == payload.phone))
    if existing is not None:
        name = existing.full_name or existing.business_name
        raise LeadConflictError(f"{payload.phone} is already a lead{f' ({name})' if name else ''}.")
    lead = MarketingLead(**payload.model_dump(), created_by=admin.id)
    session.add(lead)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise LeadConflictError(f"{payload.phone} is already a lead.") from exc
    return await _one_out(session, lead)


async def update_lead(session: AsyncSession, admin: User, lead_id: UUID, payload: LeadUpdate) -> LeadOut:
    lead = await _get(session, lead_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("phone") and changes["phone"] != lead.phone:
        if await session.scalar(select(MarketingLead.id).where(MarketingLead.phone == changes["phone"])):
            raise LeadConflictError(f"{changes['phone']} is already a lead.")
    status = changes.pop("status", None)
    for field, value in changes.items():
        if field in REQUIRED and value is None:
            continue
        setattr(lead, field, value)
    if status:
        _set_status(session, lead, status, admin)
    lead.updated_at = datetime.now(timezone.utc)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise LeadConflictError("Another lead already uses this phone number.") from exc
    return await _one_out(session, lead)


async def delete_lead(session: AsyncSession, lead_id: UUID) -> None:
    await session.delete(await _get(session, lead_id))
    await session.commit()


def _activity_out(activity: MarketingLeadActivity, author: str | None) -> ActivityOut:
    return ActivityOut(
        id=activity.id, lead_id=activity.lead_id, kind=activity.kind, text=activity.text, amount=activity.amount,
        created_by_name=author, created_at=activity.created_at,
    )


async def list_activities(session: AsyncSession, lead_id: UUID) -> list[ActivityOut]:
    """Newest first."""
    await _get(session, lead_id)
    rows = await session.execute(
        select(MarketingLeadActivity, User.full_name)
        .outerjoin(User, User.id == MarketingLeadActivity.created_by)
        .where(MarketingLeadActivity.lead_id == lead_id)
        .order_by(MarketingLeadActivity.created_at.desc(), MarketingLeadActivity.id)
    )
    return [_activity_out(activity, author) for activity, author in rows.all()]


async def add_activity(session: AsyncSession, admin: User, lead_id: UUID, payload: ActivityCreate) -> ActivityResult:
    """Log a call, message, meeting, note or payment. A first contact moves a New lead to Called and a payment
    confirms the deal (Converted); a follow-up date sent with the entry replaces the lead's follow-up."""
    lead = await _get(session, lead_id)
    # Timestamped here, not by the database, so an automatic status change logged next sorts after this entry.
    activity = MarketingLeadActivity(
        lead_id=lead.id, kind=payload.kind, text=payload.text, amount=payload.amount, created_by=admin.id,
        created_at=datetime.now(timezone.utc),
    )
    session.add(activity)
    next_status = status_after_activity(lead.status, payload.kind)
    if next_status:
        _set_status(session, lead, next_status, admin)
    if payload.follow_up_on is not None:
        lead.follow_up_on = payload.follow_up_on
    lead.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(activity)
    return ActivityResult(activity=_activity_out(activity, admin.full_name), lead=await _one_out(session, lead))


async def delete_activity(session: AsyncSession, lead_id: UUID, activity_id: UUID) -> ActivityResult:
    """Remove a mistaken entry (e.g. a payment typed wrong). Status changes it caused are kept."""
    activity = await session.get(MarketingLeadActivity, activity_id)
    if activity is None or activity.lead_id != lead_id:
        raise LeadNotFoundError("Entry not found")
    await session.delete(activity)
    await session.commit()
    return ActivityResult(activity=None, lead=await _one_out(session, await _get(session, lead_id)))
