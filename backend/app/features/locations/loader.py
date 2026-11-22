"""Loads the bundled India Post PIN directory into pincode_areas.

Runs automatically at startup when the table is empty, so a new deploy never shows bare PIN codes;
db/scripts/import_pincodes.py calls it with replace=True to refresh the data.
"""
import csv
import gzip
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)

DATA = Path(__file__).resolve().parents[4] / "db" / "data" / "pincode_areas.csv.gz"
COLUMNS = ["pincode", "area", "taluk", "district", "state"]
# Any constant works; it only stops two app instances from loading at the same time.
LOAD_LOCK_ID = 726_001


def read_rows() -> list[tuple[str, ...]]:
    with gzip.open(DATA, "rt", encoding="utf-8", newline="") as handle:
        return [tuple(row[column] for column in COLUMNS) for row in csv.DictReader(handle)]


async def load_directory(engine: AsyncEngine, replace: bool = False) -> int:
    """Copy the bundled rows in; returns how many were loaded (0 when already present and not replacing)."""
    async with engine.begin() as connection:
        await connection.execute(text("SELECT pg_advisory_xact_lock(:lock)"), {"lock": LOAD_LOCK_ID})
        if not replace and await connection.scalar(text("SELECT EXISTS (SELECT 1 FROM pincode_areas)")):
            return 0
        rows = read_rows()
        await connection.execute(text("TRUNCATE pincode_areas RESTART IDENTITY"))
        raw = await connection.get_raw_connection()
        await raw.driver_connection.copy_records_to_table("pincode_areas", records=rows, columns=COLUMNS)
        return len(rows)


async def ensure_directory_loaded(engine: AsyncEngine | None) -> None:
    """Startup hook: never blocks or crashes the app; logs if the table or data file is missing."""
    if engine is None:
        return
    try:
        loaded = await load_directory(engine)
        if loaded:
            logger.info("Loaded %s PIN code areas into pincode_areas", loaded)
    except Exception:
        logger.exception("Could not load the PIN code directory (is migration 026 applied?)")
