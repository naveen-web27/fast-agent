"""Load db/data/pincode_areas.csv.gz into the pincode_areas table (replaces existing rows).

Run once per database after migration 026, from the repository root:
    PYTHONPATH=backend python3 db/scripts/import_pincodes.py
It uses DATABASE_URL from backend/.env (or the environment). Re-running is safe.
"""
import asyncio
import csv
import gzip
from pathlib import Path

from sqlalchemy import text

from app.db.session import engine

DATA = Path(__file__).resolve().parents[1] / "data" / "pincode_areas.csv.gz"
COLUMNS = ["pincode", "area", "taluk", "district", "state"]


async def main() -> None:
    if engine is None:
        raise SystemExit("DATABASE_URL is not configured (backend/.env)")
    with gzip.open(DATA, "rt", encoding="utf-8", newline="") as handle:
        rows = [tuple(row[column] for column in COLUMNS) for row in csv.DictReader(handle)]
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE pincode_areas RESTART IDENTITY"))
        raw = await connection.get_raw_connection()
        await raw.driver_connection.copy_records_to_table("pincode_areas", records=rows, columns=COLUMNS)
        count = await connection.scalar(text("SELECT count(*) FROM pincode_areas"))
    await engine.dispose()
    print(f"Loaded {count} PIN code areas")


if __name__ == "__main__":
    asyncio.run(main())
