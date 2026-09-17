"""Read tenant/client configuration from the versioned CSV file."""
import csv
import os
import uuid
from pathlib import Path

from src.models import Business

CLIENTS_FILE = Path(__file__).resolve().parents[2] / "data" / "clients.csv"


class ClientRegistryError(Exception):
    """Raised when the client CSV is missing or contains invalid configuration."""


def get_business_by_phone_number_id(phone_number_id: str) -> Business | None:
    """Find a business by Meta's WhatsApp phone number ID without using SQLite."""
    if not CLIENTS_FILE.exists():
        raise ClientRegistryError(f"Client registry not found: {CLIENTS_FILE}")

    with CLIENTS_FILE.open(newline="", encoding="utf-8") as clients_file:
        for row in csv.DictReader(clients_file):
            if row.get("whatsapp_phone_number_id") != phone_number_id:
                continue
            return _business_from_row(row)
    return None


def _business_from_row(row: dict[str, str]) -> Business:
    try:
        business_id = uuid.UUID(row["business_id"])
    except (KeyError, ValueError) as exc:
        raise ClientRegistryError("Each client row needs a valid business_id UUID") from exc

    data_mode = (row.get("data_mode") or "hosted").strip().lower()
    if data_mode not in {"hosted", "api"}:
        raise ClientRegistryError(f"Unsupported data_mode: {data_mode}")

    api_key = None
    api_key_env = (row.get("client_api_key_env") or "").strip()
    if api_key_env:
        api_key = os.getenv(api_key_env)

    # Business is used as an in-memory tenant context; client data is sourced from CSV.
    return Business(
        id=business_id,
        name=row.get("name", "").strip(),
        whatsapp_phone_number_id=row["whatsapp_phone_number_id"].strip(),
        data_mode=data_mode,
        client_api_base_url=(row.get("client_api_base_url") or "").strip() or None,
        client_api_key=api_key,
    )
