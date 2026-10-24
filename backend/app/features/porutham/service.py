"""Report preview, one-time Razorpay purchase and paid unlock for Kattam porutham and Jathagam, free of FastAPI and DB code."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Awaitable, Callable

from app.features.payments.verification import foreign_origin, matching_payment, valid_payment_signature

from . import report

PRODUCTS = {"kattam": "kattam_report", "jathagam": "jathagam_report"}
DESCRIPTIONS = {"kattam": "Thirumana porutham report (PDF)", "jathagam": "Jathagam report (PDF)"}
ROLES = {"kattam": ("bride", "groom"), "jathagam": ("person",)}
Razorpay = Callable[[str, str, dict | None], Awaitable[dict]]


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def people(data: dict, kind: str = "kattam") -> dict:
    return {role: dict(data[role], birth_date=str(data[role]["birth_date"]), birth_time=str(data[role]["birth_time"])[:8])
            for role in ROLES[kind]}


def build(data: dict, now_ms: float | None = None, kind: str = "kattam") -> dict:
    now_ms = time.time() * 1000 if now_ms is None else now_ms
    language = data.get("language", "ta")
    try:
        if kind == "jathagam":
            return report.jathagam_report(people(data, kind)["person"], language, now_ms)
        return report.kattam_report(people(data), language, now_ms, data.get("selected"))
    except ValueError as exc:
        if str(exc) in ("nonexistent-time", "ambiguous-time"):
            raise ServiceError(422, str(exc)) from exc
        raise


def unlock_offer(settings) -> dict:
    amount = settings.razorpay_kattam_report_amount_paise
    return {"amount_paise": amount, "available": ready(settings), "pack": pack_offer(settings)}


def ready(settings) -> bool:
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret) and settings.razorpay_kattam_report_amount_paise >= 100


# Binds a payment to one couple's (or person's) birth data without sending that data to Razorpay.
def report_key(data: dict, secret: str, kind: str = "kattam") -> str:
    return hmac.new(secret.encode(), f"{kind}-report|{canonical_births(data, kind)}".encode(), hashlib.sha256).hexdigest()[:48]


def canonical_births(data: dict, kind: str = "kattam") -> str:
    births = people(data, kind)
    return json.dumps([[births[role]["birth_date"], births[role]["birth_time"], round(float(births[role]["latitude"]), 4),
                        round(float(births[role]["longitude"]), 4), births[role]["timezone"]] for role in ROLES[kind]])


def couple_key(data: dict, kind: str = "kattam") -> str:
    return hashlib.sha256(f"{kind}-couple|{canonical_births(data, kind)}".encode()).hexdigest()[:48]


def stored_inputs(data: dict, kind: str = "kattam") -> dict:
    if kind == "jathagam":
        return {"person": data["person"]}
    return {"bride": data["bride"], "groom": data["groom"], "selected": data.get("selected")}


def history_summary(entry) -> dict:
    return {"id": str(entry.id), "kind": entry.kind, "bride": entry.bride_name, "groom": entry.groom_name, "level": entry.level,
            "stars": entry.stars_matched, "kattam": entry.kattam_matched, "unlocked": entry.unlocked,
            "updated_at": entry.updated_at.isoformat()}


def credits_left(packs, now) -> int:
    return sum(pack.reports_total - pack.reports_used for pack in packs
               if pack.status == "paid" and pack.expires_at and pack.expires_at > now and pack.reports_used < pack.reports_total)


def pack_offer(settings) -> dict:
    amount = settings.razorpay_porutham_pack_amount_paise
    return {"amount_paise": amount, "reports": settings.porutham_pack_reports, "days": settings.porutham_pack_days,
            "available": bool(settings.razorpay_key_id and settings.razorpay_key_secret) and amount >= 100
            and settings.porutham_pack_reports > 0 and settings.porutham_pack_days > 0}


async def create_order(data: dict, settings, razorpay: Razorpay, kind: str = "kattam") -> dict:
    if not ready(settings):
        raise ServiceError(503, "Report checkout is not available yet")
    build(data, kind=kind)
    amount = settings.razorpay_kattam_report_amount_paise
    order = await razorpay("POST", "orders", {
        "amount": amount, "currency": "INR", "receipt": f"{kind}-{uuid.uuid4().hex[:24]}",
        "notes": {"rightconnect_product": PRODUCTS[kind], "rightconnect_origin": settings.app_base_url.rstrip("/"),
                  "report_key": report_key(data, settings.razorpay_key_secret, kind)},
    })
    order_id = order.get("id")
    if not isinstance(order_id, str) or not order_id.startswith("order_") or order.get("amount") != amount or order.get("currency") != "INR":
        raise ServiceError(500, "Invalid order returned by provider")
    return {"order_id": order_id, "amount": amount, "currency": "INR", "key_id": settings.razorpay_key_id,
            "description": DESCRIPTIONS[kind]}


async def unlock(data: dict, settings, razorpay: Razorpay, now_ms: float | None = None, kind: str = "kattam") -> dict:
    proof = data["payment"]
    order_id, payment_id = proof["razorpay_order_id"], proof["razorpay_payment_id"]
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ServiceError(503, "Payment verification is unavailable")
    if not valid_payment_signature(order_id, payment_id, proof["razorpay_signature"], settings.razorpay_key_secret):
        raise ServiceError(400, "Invalid payment signature")
    order = await razorpay("GET", f"orders/{order_id}", None)
    notes = order.get("notes")
    amount = order.get("amount")
    if order.get("id") != order_id or not isinstance(notes, dict) or notes.get("rightconnect_product") != PRODUCTS[kind] \
            or foreign_origin(order, settings.app_base_url) or order.get("currency") != "INR" \
            or not isinstance(amount, int) or amount < 100 \
            or not hmac.compare_digest(str(notes.get("report_key", "")), report_key(data, settings.razorpay_key_secret, kind)):
        raise ServiceError(400, "This payment is not for these birth details")
    captured = await razorpay("GET", f"payments/{payment_id}", None)
    if not matching_payment(captured, order_id, amount, payment_id):
        raise ServiceError(400, "Payment details do not match")
    if captured["status"] != "captured":
        return {"status": "pending", "detail": "Payment authorized; awaiting capture. Do not pay again."}
    return {"status": "paid", "report": build(data, now_ms, kind)}
