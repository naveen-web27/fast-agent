"""Server-side Thirumana porutham: free Rasi check, Kattam preview, paid reports, history and report packs."""
import time
from datetime import datetime, timezone
from functools import partial
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.payments.router import razorpay_api
from app.features.payments.verification import matching_payment, valid_payment_signature
from app.models.porutham import PoruthamPack
from app.security.dependencies import bearer_scheme, get_current_auth_user_id

from . import report, service, store
from .contracts import KattamRequest, PaymentProof, RasiRequest, UnlockRequest

router = APIRouter()


def failure(exc: service.ServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


async def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db),
) -> UUID | None:
    return None if credentials is None else await get_current_auth_user_id(credentials, settings, session)


def build(data: dict, now_ms: float) -> dict:
    try:
        return service.build(data, now_ms)
    except service.ServiceError as exc:
        raise failure(exc) from exc


def moment(now_ms: float) -> datetime:
    return datetime.fromtimestamp(now_ms / 1000, timezone.utc)


async def remember(session: AsyncSession, user: UUID | None, data: dict, full: dict, now_ms: float,
                   unlocked: bool, settings: Settings) -> dict:
    """Saves a signed-in check to history and reports whether the full report may be shown."""
    if user is None:
        return {"unlocked": unlocked, "history_id": None}
    admin = await store.is_admin(session, user, settings)
    entry = await store.save_history(session, user, data, full, moment(now_ms), unlocked or admin, store.history_limit(settings, admin))
    await session.commit()
    return {"unlocked": entry.unlocked, "history_id": str(entry.id)}


@router.post("/rasi")
def rasi_porutham(body: RasiRequest) -> dict:
    data = body.model_dump()
    return report.rasi_report(data["bride"], data["groom"], body.language)


@router.post("/kattam")
async def kattam_preview(body: KattamRequest, user: UUID | None = Depends(optional_user),
                         session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    data, now_ms = body.model_dump(mode="json"), time.time() * 1000
    full = build(data, now_ms)
    saved = await remember(session, user, data, full, now_ms, False, settings)
    return {"report": full if saved["unlocked"] else report.preview(full, body.language),
            "unlock": service.unlock_offer(settings), "history_id": saved["history_id"]}


@router.post("/kattam/order")
async def kattam_order(body: KattamRequest, settings: Settings = Depends(get_settings)) -> dict:
    try:
        return await service.create_order(body.model_dump(mode="json"), settings, partial(razorpay_api, settings))
    except service.ServiceError as exc:
        raise failure(exc) from exc


@router.post("/kattam/full")
async def kattam_full(body: UnlockRequest, user: UUID | None = Depends(optional_user),
                      session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    data, now_ms = body.model_dump(mode="json"), time.time() * 1000
    try:
        result = await service.unlock(data, settings, partial(razorpay_api, settings), now_ms)
    except service.ServiceError as exc:
        raise failure(exc) from exc
    if result["status"] == "paid":
        await remember(session, user, data, result["report"], now_ms, True, settings)
    return result


@router.post("/kattam/credit")
async def kattam_credit(body: KattamRequest, user: UUID = Depends(get_current_auth_user_id),
                        session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    data, now_ms = body.model_dump(mode="json"), time.time() * 1000
    full = build(data, now_ms)
    existing = await store.find_history(session, user, service.couple_key(data))
    already = (existing is not None and existing.unlocked) or await store.is_admin(session, user, settings)
    if not already and not await store.use_credit(session, user, moment(now_ms)):
        raise HTTPException(status_code=402, detail="No reports left in your pack")
    await remember(session, user, data, full, now_ms, True, settings)
    return {"status": "paid", "report": full}


@router.get("/me")
async def account(user: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db),
                  settings: Settings = Depends(get_settings)) -> dict:
    admin = await store.is_admin(session, user, settings)
    limit = store.history_limit(settings, admin)
    now = datetime.now(timezone.utc)
    packs = await store.active_packs(session, user, now)
    entries = await store.history(session, user, limit)
    return {"admin": admin, "credits": service.credits_left(packs, now),
            "pack_expires_at": max((pack.expires_at for pack in packs), default=None),
            "history_limit": limit, "history": [service.history_summary(entry) for entry in entries],
            "last_inputs": entries[0].inputs if entries else None, "pack": service.pack_offer(settings)}


@router.get("/history/{entry_id}")
async def history_report(entry_id: UUID, language: Literal["ta", "en"] = "ta", user: UUID = Depends(get_current_auth_user_id),
                         session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict:
    entry = await store.history_entry(session, user, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="History entry not found")
    full = build(dict(entry.inputs, language=language), entry.report_at.timestamp() * 1000)
    unlocked = entry.unlocked or await store.is_admin(session, user, settings)
    return {"id": str(entry.id), "inputs": entry.inputs, "report": full if unlocked else report.preview(full, language),
            "unlock": service.unlock_offer(settings)}


@router.delete("/history/{entry_id}", status_code=204)
async def delete_history(entry_id: UUID, user: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)) -> None:
    if not await store.delete_history(session, user, entry_id):
        raise HTTPException(status_code=404, detail="History entry not found")
    await session.commit()


@router.post("/pack/order")
async def pack_order(user: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db),
                     settings: Settings = Depends(get_settings)) -> dict:
    offer = service.pack_offer(settings)
    if not offer["available"]:
        raise HTTPException(status_code=503, detail="Report packs are not available yet")
    pack = PoruthamPack(auth_user_id=user, amount_paise=offer["amount_paise"], reports_total=offer["reports"], days=offer["days"])
    session.add(pack)
    await session.flush()
    order = await razorpay_api(settings, "POST", "orders", {
        "amount": pack.amount_paise, "currency": "INR", "receipt": f"pack-{pack.id.hex[:24]}",
        "notes": {"rightconnect_product": "porutham_pack", "rightconnect_pack_id": str(pack.id),
                  "rightconnect_origin": settings.app_base_url.rstrip("/")},
    })
    order_id = order.get("id")
    if not isinstance(order_id, str) or not order_id.startswith("order_") or order.get("amount") != pack.amount_paise \
            or order.get("currency") != "INR":
        raise HTTPException(status_code=500, detail="Invalid order returned by provider")
    pack.razorpay_order_id = order_id
    await session.commit()
    return {"order_id": order_id, "amount": pack.amount_paise, "currency": "INR", "key_id": settings.razorpay_key_id,
            "reports": pack.reports_total, "days": pack.days}


@router.post("/pack/verify")
async def pack_verify(proof: PaymentProof, user: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db),
                      settings: Settings = Depends(get_settings)) -> dict:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=503, detail="Payment verification is unavailable")
    pack = await session.scalar(select(PoruthamPack).where(
        PoruthamPack.razorpay_order_id == proof.razorpay_order_id, PoruthamPack.auth_user_id == user).with_for_update())
    if pack is None:
        raise HTTPException(status_code=400, detail="Unknown pack order for this account")
    if not valid_payment_signature(pack.razorpay_order_id, proof.razorpay_payment_id, proof.razorpay_signature, settings.razorpay_key_secret):
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    if pack.status != "paid":
        captured = await razorpay_api(settings, "GET", f"payments/{proof.razorpay_payment_id}")
        if not matching_payment(captured, pack.razorpay_order_id, pack.amount_paise, proof.razorpay_payment_id):
            raise HTTPException(status_code=400, detail="Payment details do not match")
        if captured["status"] != "captured":
            return {"status": "pending", "detail": "Payment authorized; awaiting capture. Do not pay again."}
        store.activate_pack(pack, proof.razorpay_payment_id)
        await session.commit()
    return {"status": "paid", "credits": pack.reports_total - pack.reports_used, "expires_at": pack.expires_at.isoformat()}
