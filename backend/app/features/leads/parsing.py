"""Pure helpers for leads: clean phone numbers and read free-text type/status/date values from pasted spreadsheets."""
import re
from datetime import date, datetime

LEAD_TYPES = ("unknown", "customer", "expert", "company", "worker")
LEAD_STATUSES = ("new", "contacted", "interested", "follow_up", "not_interested", "signed_up")

_TYPE_WORDS = (
    ("worker", ("worker", "labour", "labor", "job seeker", "jobseeker", "staff", "driver", "cook", "helper", "electrician", "plumber")),
    ("company", ("company", "business", "shop", "store", "firm", "agency", "owner", "hotel", "restaurant", "clinic", "pvt", "ltd")),
    ("expert", ("expert", "consultant", "advisor", "adviser", "freelancer", "professional", "doctor", "lawyer", "astrologer", "tutor")),
    ("customer", ("customer", "client", "buyer", "user")),
)
# Checked in order, so "not interested" wins over "interested".
_STATUS_WORDS = (
    ("not_interested", ("not interested", "no interest", "rejected", "dead", "lost")),
    ("signed_up", ("signed up", "signup", "registered", "joined", "converted", "profile created")),
    ("follow_up", ("follow up", "followup", "call back", "callback", "later")),
    ("interested", ("interested", "hot", "warm")),
    ("contacted", ("contacted", "called", "messaged", "pitched", "no response")),
    ("new", ("new", "fresh", "pending")),
)


def clean_phone(value: str | None) -> str:
    """Return an E.164 number (+919876543210) from what people type or paste, e.g. "98765 43210", "+91-98765-43210",
    "919876543210" or "09876543210". Raises ValueError when it can't be a phone number."""
    raw = (value or "").strip()
    # Excel number cells can paste as "9876543210.0".
    raw = re.sub(r"\.0+$", "", raw)
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+") or raw.startswith("00"):
        digits = digits[2:] if raw.startswith("00") else digits
        if 8 <= len(digits) <= 15 and digits[0] != "0":
            return f"+{digits}"
    elif len(digits) == 10 and digits[0] in "6789":
        return f"+91{digits}"
    elif len(digits) == 11 and digits[0] == "0" and digits[1] in "6789":
        return f"+91{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return f"+{digits}"
    raise ValueError(f"\"{raw[:30]}\" is not a phone number. Use a 10-digit mobile number or add the country code (+...).")


def _words(text: str | None) -> str:
    return " ".join((text or "").lower().replace("-", " ").replace("_", " ").split())


def _match(text: str | None, table, default):
    words = _words(text)
    if not words:
        return default
    for value, keywords in table:
        if words == _words(value) or any(re.search(rf"\b{re.escape(keyword)}\b", words) for keyword in keywords):
            return value
    return default


def guess_type(text: str | None) -> str:
    """'Shop owner' -> company, 'Driver' -> worker, 'Consultant' -> expert; anything else -> unknown."""
    return _match(text, _TYPE_WORDS, "unknown")


def guess_status(text: str | None) -> str | None:
    """'Called' -> contacted, 'Call back' -> follow_up ...; None when blank or unrecognised."""
    return _match(text, _STATUS_WORDS, None)


def parse_date(text: str | None) -> date | None:
    """2026-12-05, 05/12/2026, 5-12-2026 or 05.12.26 (day first, as in India); None when blank or not a date."""
    value = (text or "").strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def clip(value: str | None, limit: int) -> str | None:
    """Collapse spaces and cut to `limit` characters; blank -> None."""
    text = " ".join(str(value or "").split())[:limit]
    return text or None
