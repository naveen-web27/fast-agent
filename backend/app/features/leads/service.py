"""Admin lead management: track enquiries, import pasted spreadsheets, and see which leads already have a profile."""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.leads.parsing import clean_phone, clip, guess_status, guess_type, parse_date
from app.features.leads.schemas import (
    LeadCreate,
    LeadImport,
    LeadImportError,
    LeadImportResult,
    LeadOut,
    LeadUpdate,
    ProfileMatch,
)
from app.models.lead import Lead
from app.models.profile import Organization, Profile, ProfileKind
from app.models.user import User
from app.models.worker import WorkerProfile

ROLE_LABELS = {"customer": "Customer", "expert": "Expert", "company_admin": "Company admin", "worker": "Worker", "platform_admin": "Admin"}
INDIA_TIME = timezone(timedelta(hours=5, minutes=30))
TEXT_LIMITS = {"full_name": 120, "business_name": 160, "service": 120, "city": 100, "source": 80}


class LeadNotFoundError(Exception):
    """The lead doesn't exist."""


class LeadConflictError(Exception):
    """Another lead already uses this phone number."""


def _like(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def profile_matches(session: AsyncSession, phones: list[str]) -> dict[str, list[ProfileMatch]]:
    """phone -> accounts, workers, companies and experts on RightConnect using that number."""
    found: dict[str, list[ProfileMatch]] = {}
    if not phones:
        return found

    def add(phone: str | None, kind: str, label: str) -> None:
        if phone:
            matches = found.setdefault(phone, [])
            if not any(match.kind == kind and match.label == label for match in matches):
                matches.append(ProfileMatch(kind=kind, label=label))

    for phone, name, role in (
        await session.execute(select(User.phone, User.full_name, User.role).where(User.phone.in_(phones), User.deleted_at.is_(None)))
    ).all():
        role_value = getattr(role, "value", role)
        add(phone, "account", f"{name} ({ROLE_LABELS.get(role_value, role_value)})")
    for phone, name in (
        await session.execute(
            select(WorkerProfile.contact_phone, WorkerProfile.display_name)
            .where(WorkerProfile.contact_phone.in_(phones), WorkerProfile.deleted_at.is_(None))
        )
    ).all():
        add(phone, "worker", name)
    for phone, name in (
        await session.execute(
            select(Organization.contact_phone, Organization.name)
            .where(Organization.contact_phone.in_(phones), Organization.deleted_at.is_(None))
        )
    ).all():
        add(phone, "company", name)
    for phone, name, kind in (
        await session.execute(
            select(Profile.contact_phone, Profile.display_name, Profile.kind)
            .where(Profile.contact_phone.in_(phones), Profile.deleted_at.is_(None))
        )
    ).all():
        add(phone, "expert" if kind == ProfileKind.EXPERT else "company", name)
    return found


def _out(lead: Lead, matches: dict[str, list[ProfileMatch]]) -> LeadOut:
    return LeadOut(
        id=lead.id, full_name=lead.full_name, phone=lead.phone, lead_type=lead.lead_type,
        business_name=lead.business_name, service=lead.service, city=lead.city, source=lead.source,
        status=lead.status, follow_up_on=lead.follow_up_on, notes=lead.notes,
        created_at=lead.created_at, updated_at=lead.updated_at, matches=matches.get(lead.phone, []),
    )


async def _one_out(session: AsyncSession, lead: Lead) -> LeadOut:
    await session.refresh(lead)
    return _out(lead, await profile_matches(session, [lead.phone]))


async def list_leads(
    session: AsyncSession,
    status: str | None = None,
    lead_type: str | None = None,
    query: str | None = None,
    profile: str | None = None,
    due: bool = False,
) -> list[LeadOut]:
    """Newest first. profile='missing' keeps leads whose number isn't on RightConnect yet; due=True keeps follow-ups due
    today or earlier (excluding signed-up and not-interested leads)."""
    stmt = select(Lead)
    if status:
        stmt = stmt.where(Lead.status == status)
    if lead_type:
        stmt = stmt.where(Lead.lead_type == lead_type)
    if query and query.strip():
        pattern = _like(query.strip())
        digits = "".join(ch for ch in query if ch.isdigit())
        conditions = [
            column.ilike(pattern, escape="\\")
            for column in (Lead.full_name, Lead.business_name, Lead.service, Lead.city, Lead.notes, Lead.source)
        ]
        if len(digits) >= 3:
            conditions.append(Lead.phone.like(f"%{digits}%"))
        stmt = stmt.where(or_(*conditions))
    if due:
        stmt = stmt.where(
            Lead.follow_up_on.is_not(None),
            Lead.follow_up_on <= datetime.now(INDIA_TIME).date(),
            Lead.status.not_in(("signed_up", "not_interested")),
        )
        stmt = stmt.order_by(Lead.follow_up_on, Lead.created_at.desc())
    else:
        stmt = stmt.order_by(Lead.created_at.desc())
    leads = (await session.scalars(stmt.limit(2000))).all()
    matches = await profile_matches(session, [lead.phone for lead in leads])
    results = [_out(lead, matches) for lead in leads]
    if profile == "missing":
        results = [lead for lead in results if not lead.matches]
    elif profile == "created":
        results = [lead for lead in results if lead.matches]
    return results


async def create_lead(session: AsyncSession, admin: User, payload: LeadCreate) -> LeadOut:
    existing = await session.scalar(select(Lead).where(Lead.phone == payload.phone))
    if existing is not None:
        raise LeadConflictError(f"{payload.phone} is already a lead{f' ({existing.full_name})' if existing.full_name else ''}.")
    lead = Lead(**payload.model_dump(), created_by=admin.id)
    session.add(lead)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise LeadConflictError(f"{payload.phone} is already a lead.") from exc
    return await _one_out(session, lead)


async def update_lead(session: AsyncSession, lead_id: UUID, payload: LeadUpdate) -> LeadOut:
    lead = await session.get(Lead, lead_id)
    if lead is None:
        raise LeadNotFoundError("Lead not found")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("phone") and changes["phone"] != lead.phone:
        if await session.scalar(select(Lead.id).where(Lead.phone == changes["phone"])):
            raise LeadConflictError(f"{changes['phone']} is already a lead.")
    for field, value in changes.items():
        if field in ("phone", "lead_type", "status") and value is None:
            continue
        setattr(lead, field, value)
    lead.updated_at = datetime.now(timezone.utc)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise LeadConflictError("Another lead already uses this phone number.") from exc
    return await _one_out(session, lead)


async def delete_lead(session: AsyncSession, lead_id: UUID) -> None:
    lead = await session.get(Lead, lead_id)
    if lead is None:
        raise LeadNotFoundError("Lead not found")
    await session.delete(lead)
    await session.commit()


def clean_import_row(row, default_source: str | None) -> dict:
    """One pasted row -> lead fields. Raises ValueError (with a readable message) when the phone is missing or wrong."""
    if not (row.phone or "").strip():
        raise ValueError("No phone number")
    fields = {field: clip(getattr(row, field), limit) for field, limit in TEXT_LIMITS.items()}
    fields["source"] = fields["source"] or clip(default_source, TEXT_LIMITS["source"])
    notes = (row.notes or "").strip()[:2000]
    return {
        **fields,
        "phone": clean_phone(row.phone),
        "lead_type": guess_type(row.lead_type),
        "status": guess_status(row.status),
        "follow_up_on": parse_date(row.follow_up_on),
        "notes": notes or None,
    }


def merge_into(lead: Lead, fields: dict) -> bool:
    """Fill the existing lead's empty fields from an imported row; a new note is added below the old one.
    Nothing already entered is overwritten. Returns True when anything changed."""
    changed = False
    for field in ("full_name", "business_name", "service", "city", "source", "follow_up_on"):
        if fields.get(field) and not getattr(lead, field):
            setattr(lead, field, fields[field])
            changed = True
    if fields.get("lead_type") not in (None, "unknown") and lead.lead_type == "unknown":
        lead.lead_type = fields["lead_type"]
        changed = True
    if fields.get("status") and lead.status == "new" and fields["status"] != "new":
        lead.status = fields["status"]
        changed = True
    note = fields.get("notes")
    if note and note not in (lead.notes or ""):
        lead.notes = f"{lead.notes}\n{note}"[:2000] if lead.notes else note
        changed = True
    return changed


async def import_leads(session: AsyncSession, admin: User, payload: LeadImport) -> LeadImportResult:
    """Add pasted rows. A number that's already a lead (or repeated in the paste) only fills in empty fields."""
    errors: list[LeadImportError] = []
    cleaned: dict[str, dict] = {}
    for index, row in enumerate(payload.rows, start=1):
        try:
            fields = clean_import_row(row, payload.source)
        except ValueError as exc:
            errors.append(LeadImportError(row=index, message=str(exc)))
            continue
        if fields["phone"] in cleaned:
            merge_into(_Draft(cleaned[fields["phone"]]), fields)
        else:
            cleaned[fields["phone"]] = fields
    existing = {
        lead.phone: lead
        for lead in (await session.scalars(select(Lead).where(Lead.phone.in_(list(cleaned))))).all()
    } if cleaned else {}
    created = updated = 0
    now = datetime.now(timezone.utc)
    for phone, fields in cleaned.items():
        lead = existing.get(phone)
        if lead is None:
            session.add(Lead(**{**fields, "status": fields["status"] or "new"}, created_by=admin.id))
            created += 1
        elif merge_into(lead, fields):
            lead.updated_at = now
            updated += 1
    await session.commit()
    return LeadImportResult(created=created, updated=updated, errors=errors)


class _Draft:
    """Lets merge_into fill a not-yet-saved row (a dict) the same way it fills a saved lead."""

    def __init__(self, fields: dict):
        object.__setattr__(self, "_fields", fields)

    def __getattr__(self, name):
        value = self._fields.get(name)
        if name == "lead_type":
            return value or "unknown"
        if name == "status":
            return value or "new"
        return value

    def __setattr__(self, name, value):
        self._fields[name] = value
