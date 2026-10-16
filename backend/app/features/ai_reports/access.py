"""Dependency-free capability validation and safe public failure messages."""
import base64
import hashlib
import hmac
import re
from uuid import UUID


ERROR_MESSAGES = {
    "calculation_failed": "The report calculation could not be completed.",
    "writer_failed": "The report could not be written. Please retry.",
    "writer_timeout": "The report writer timed out. Please retry.",
    "generation_failed": "The report could not be completed. Please retry.",
}


def capability_hash(token: str) -> str:
    if not isinstance(token, str) or re.fullmatch(r"[A-Za-z0-9_-]{43}", token) is None:
        raise ValueError("A valid X-Report-Token is required")
    decoded = base64.urlsafe_b64decode(token + "=")
    if len(decoded) != 32 or base64.urlsafe_b64encode(decoded).decode().rstrip("=") != token:
        raise ValueError("A valid X-Report-Token is required")
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def can_access(owner_id: UUID | None, user_id: UUID | None, stored_hash: str, token: str | None) -> bool:
    if isinstance(owner_id, UUID) and isinstance(user_id, UUID) and owner_id == user_id:
        return True
    if token is None:
        return False
    try:
        supplied_hash = capability_hash(token)
    except ValueError:
        return False
    return hmac.compare_digest(stored_hash, supplied_hash)


def safe_error_code(code: str | None) -> str:
    return code if code in ERROR_MESSAGES else "generation_failed"


def client_hash(salt: str, host: str) -> str:
    if not salt:
        raise ValueError("AI report rate limiting is not configured")
    return hmac.new(salt.encode(), host.encode(), hashlib.sha256).hexdigest()