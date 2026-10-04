"""Turn whatever link a user pastes into a safe https URL and a friendly platform name."""
import re
from urllib.parse import urlparse

# Host suffix -> label shown on profiles. Anything else is a "Website".
PLATFORMS: list[tuple[str, str]] = [
    ("instagram.com", "Instagram"),
    ("youtube.com", "YouTube"),
    ("youtu.be", "YouTube"),
    ("linkedin.com", "LinkedIn"),
    ("facebook.com", "Facebook"),
    ("fb.com", "Facebook"),
    ("x.com", "X"),
    ("twitter.com", "X"),
    ("github.com", "GitHub"),
    ("wa.me", "WhatsApp"),
    ("whatsapp.com", "WhatsApp"),
    ("t.me", "Telegram"),
    ("behance.net", "Behance"),
    ("dribbble.com", "Dribbble"),
    ("medium.com", "Medium"),
    ("threads.net", "Threads"),
    ("pinterest.com", "Pinterest"),
]


def normalize_url(value: str) -> str:
    """Accept "instagram.com/me" or "https://..."; reject anything that isn't a plain web link."""
    value = value.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", value, flags=re.IGNORECASE):
        value = f"https://{value}"
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.hostname or "." not in parsed.hostname or re.search(r"\s", value):
        raise ValueError("Enter a valid link, e.g. instagram.com/yourname")
    return value


def detect_platform(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    for suffix, label in PLATFORMS:
        if host == suffix or host.endswith(f".{suffix}"):
            return label
    return "Website"
