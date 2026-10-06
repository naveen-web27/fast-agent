"""Provider payload validation independent of HTTP and database access."""
import hashlib
import hmac


def valid_payment_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()
    return bool(secret) and hmac.compare_digest(signature.encode(), expected.encode())


def matching_payment(entity: dict, order_id: str, amount: int, payment_id: str) -> bool:
    return (
        entity.get("id") == payment_id
        and entity.get("order_id") == order_id
        and entity.get("amount") == amount
        and entity.get("currency") == "INR"
        and entity.get("status") in ("authorized", "captured")
    )


def foreign_origin(entity: dict, app_base_url: str) -> bool:
    notes = entity.get("notes") or {}
    origin = notes.get("rightconnect_origin") if isinstance(notes, dict) else None
    return bool(origin) and origin != app_base_url.rstrip("/")