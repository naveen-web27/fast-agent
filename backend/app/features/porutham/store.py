"""Database access for signed-in porutham history, admin access and prepaid packs."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.porutham import PoruthamHistory, PoruthamPack
from app.models.user import UserRole, active_user_by_auth_id

from . import service


async def is_admin(session: AsyncSession, auth_user_id: UUID, settings) -> bool:
    user = await session.scalar(active_user_by_auth_id(auth_user_id))
    if user is None or user.role is not UserRole.PLATFORM_ADMIN:
        return False
    allowed = settings.admin_email_list
    return not allowed or (user.email or "").lower() in allowed


def history_limit(settings, admin: bool) -> int:
    return settings.porutham_admin_history_limit if admin else settings.porutham_history_limit


async def find_history(session: AsyncSession, auth_user_id: UUID, key: str) -> PoruthamHistory | None:
    return await session.scalar(select(PoruthamHistory).where(
        PoruthamHistory.auth_user_id == auth_user_id, PoruthamHistory.couple_key == key))


async def save_history(session: AsyncSession, auth_user_id: UUID, data: dict, full: dict, report_at: datetime,
                       unlocked: bool, limit: int, kind: str = "kattam") -> PoruthamHistory:
    key = service.couple_key(data, kind)
    entry = await find_history(session, auth_user_id, key)
    if entry is None:
        entry = PoruthamHistory(auth_user_id=auth_user_id, couple_key=key, kind=kind)
        session.add(entry)
    names = full["names"]
    entry.bride_name = names.get("bride", names.get("person", ""))[:100]
    entry.groom_name = names.get("groom", "")[:100]
    entry.inputs = service.stored_inputs(data, kind)
    entry.level = full["verdict"]["level"]
    entry.stars_matched = full["score"]["stars"]
    entry.kattam_matched = full["score"]["kattam"]
    entry.unlocked = bool(entry.unlocked) or unlocked
    entry.report_at = report_at
    entry.updated_at = datetime.now(timezone.utc)
    await session.flush()
    # Keep only the newest `limit` results per account; the oldest drops off first.
    keep = select(PoruthamHistory.id).where(PoruthamHistory.auth_user_id == auth_user_id) \
        .order_by(PoruthamHistory.updated_at.desc()).limit(limit)
    await session.execute(delete(PoruthamHistory).where(
        PoruthamHistory.auth_user_id == auth_user_id, PoruthamHistory.id.not_in(keep)))
    return entry


async def history(session: AsyncSession, auth_user_id: UUID, limit: int) -> list[PoruthamHistory]:
    return list(await session.scalars(select(PoruthamHistory).where(PoruthamHistory.auth_user_id == auth_user_id)
                                      .order_by(PoruthamHistory.updated_at.desc()).limit(limit)))


async def history_entry(session: AsyncSession, auth_user_id: UUID, entry_id: UUID) -> PoruthamHistory | None:
    return await session.scalar(select(PoruthamHistory).where(
        PoruthamHistory.id == entry_id, PoruthamHistory.auth_user_id == auth_user_id))


async def delete_history(session: AsyncSession, auth_user_id: UUID, entry_id: UUID) -> bool:
    result = await session.execute(delete(PoruthamHistory).where(
        PoruthamHistory.id == entry_id, PoruthamHistory.auth_user_id == auth_user_id))
    return bool(result.rowcount)


async def active_packs(session: AsyncSession, auth_user_id: UUID, now: datetime, lock: bool = False) -> list[PoruthamPack]:
    query = select(PoruthamPack).where(
        PoruthamPack.auth_user_id == auth_user_id, PoruthamPack.status == "paid", PoruthamPack.expires_at > now,
        PoruthamPack.reports_used < PoruthamPack.reports_total).order_by(PoruthamPack.expires_at)
    return list(await session.scalars(query.with_for_update() if lock else query))


async def use_credit(session: AsyncSession, auth_user_id: UUID, now: datetime) -> bool:
    packs = await active_packs(session, auth_user_id, now, lock=True)
    if not packs:
        return False
    packs[0].reports_used += 1
    return True


def activate_pack(pack: PoruthamPack, payment_id: str) -> None:
    if pack.status == "paid":
        return
    now = datetime.now(timezone.utc)
    pack.status = "paid"
    pack.razorpay_payment_id = payment_id
    pack.paid_at = now
    pack.expires_at = now + timedelta(days=pack.days)
