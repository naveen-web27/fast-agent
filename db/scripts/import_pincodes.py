"""Load (or refresh) db/data/pincode_areas.csv.gz into the pincode_areas table.

The API also does this automatically at startup when the table is empty, so this is only needed to
refresh the data after rebuilding the file. From the repository root:
    PYTHONPATH=backend python3 db/scripts/import_pincodes.py
It uses DATABASE_URL from backend/.env (or the environment). Re-running is safe.
"""
import asyncio

from app.db.session import engine
from app.features.locations.loader import load_directory


async def main() -> None:
    if engine is None:
        raise SystemExit("DATABASE_URL is not configured (backend/.env)")
    count = await load_directory(engine, replace=True)
    await engine.dispose()
    print(f"Loaded {count} PIN code areas")


if __name__ == "__main__":
    asyncio.run(main())
