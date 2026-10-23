"""Kattam report preview, one-time Razorpay purchase and paid unlock, free of FastAPI and database code."""
from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Awaitable, Callable

from app.features.payments.verification import foreign_origin, matching_payment, valid_payment_signature

from . import report

PRODUCT = "kattam_report"
Razorpay = Callable[[str, str, dict | None], Awaitable[dict]]


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def people(data: dict) -> dict:
    return {role: dict(data[role], birth_date=str(data[role]["birth_date"]), birth_time=str(data[role]["birth_time"])[:8])
            for role in ("bride", "groom")}


def build(data: dict, now_ms: float | None = None) -> dict:
    try:
        return report.kattam_report(people(data), data.get("language", "ta"),
                                    time.time() * 1000 if now_ms is None else now_ms, data.get("selected"))
    except ValueError as exc:
        if str(exc) in ("nonexistent-time", "ambiguous-time"):
            raise ServiceError(422, str(exc)) from exc
        raise


def unlock_offer(settings) -> dict:
    amount = settings.razorpay_kattam_report_amount_paise
    return {"amount_paise": amount, "available": ready(settings)}


def ready(settings) -> bool:
    return bool(settings.razorpay_key_id and settings.razorpay_key_secret) and settings.razorpay_kattam_report_amount_paise >= 100


# Binds a payment to one couple's birth data without sending that data to Razorpay.
def report_key(data: dict, secret: str) -> str:
    births = people(data)
    canonical = json.dumps([[births[role]["birth_date"], births[role]["birth_time"], round(float(births[role]["latitude"]), 4),
                             round(float(births[role]["longitude"]), 4), births[role]["timezone"]] for role in ("bride", "groom")])
    return hmac.new(secret.encode(), f"kattam-report|{canonical}".encode(), hashlib.sha256).hexdigest()[:48]


async def create_order(data: dict, settings, razorpay: Razorpay) -> dict:
    if not ready(settings):
        raise ServiceError(503, "Report checkout is not available yet")
    build(data)
    amount = settings.razorpay_kattam_report_amount_paise
    order = await razorpay("POST", "orders", {
        "amount": amount, "currency": "INR", "receipt": f"kattam-{uuid.uuid4().hex[:24]}",
        "notes": {"rightconnect_product": PRODUCT, "rightconnect_origin": settings.app_base_url.rstrip("/"),
                  "report_key": report_key(data, settings.razorpay_key_secret)},
    })
    order_id = order.get("id")
    if not isinstance(order_id, str) or not order_id.startswith("order_") or order.get("amount") != amount or order.get("currency") != "INR":
        raise ServiceError(500, "Invalid order returned by provider")
    return {"order_id": order_id, "amount": amount, "currency": "INR", "key_id": settings.razorpay_key_id,
            "description": "Thirumana porutham report (PDF)"}


async def unlock(data: dict, settings, razorpay: Razorpay, now_ms: float | None = None) -> dict:
    proof = data["payment"]
    order_id, payment_id = proof["razorpay_order_id"], proof["razorpay_payment_id"]
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise ServiceError(503, "Payment verification is unavailable")
    if not valid_payment_signature(order_id, payment_id, proof["razorpay_signature"], settings.razorpay_key_secret):
        raise ServiceError(400, "Invalid payment signature")
    order = await razorpay("GET", f"orders/{order_id}", None)
    notes = order.get("notes")
    amount = order.get("amount")
    if order.get("id") != order_id or not isinstance(notes, dict) or notes.get("rightconnect_product") != PRODUCT \
            or foreign_origin(order, settings.app_base_url) or order.get("currency") != "INR" \
            or not isinstance(amount, int) or amount < 100 \
            or not hmac.compare_digest(str(notes.get("report_key", "")), report_key(data, settings.razorpay_key_secret)):
        raise ServiceError(400, "This payment is not for these birth details")
    captured = await razorpay("GET", f"payments/{payment_id}", None)
    if not matching_payment(captured, order_id, amount, payment_id):
        raise ServiceError(400, "Payment details do not match")
    if captured["status"] != "captured":
        return {"status": "pending", "detail": "Payment authorized; awaiting capture. Do not pay again."}
    return {"status": "paid", "report": build(data, now_ms)}
