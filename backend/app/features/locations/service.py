"""Find PIN codes by place name: "Edappadi", "Salem", "Velachery" or a (partial) PIN code."""
import re
from typing import Literal

from pydantic import BaseModel
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pincode import PincodeArea

RESULT_LIMIT = 50


class Place(BaseModel):
    pincode: str
    area: str
    taluk: str
    district: str
    state: str
    # Why it matched, so the picker can explain "in Salem district" results.
    matched_on: Literal["pincode", "area", "taluk", "district"]


def clean_query(raw: str) -> tuple[str, str] | None:
    """('pincode', '6370') for digits, ('name', 'edappadi') for words, None when too short to search."""
    text = " ".join(raw.lower().split())[:60]
    digits = text.replace(" ", "")
    if digits.isdigit():
        return ("pincode", digits[:6]) if len(digits) >= 3 else None
    text = re.sub(r"[^a-z0-9 .&()-]", "", text).strip()
    return ("name", text) if len(text) >= 2 else None


def _prefix(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def _matched_on(row: PincodeArea, text: str) -> str:
    if row.area.lower().startswith(text):
        return "area"
    if row.taluk.lower().startswith(text):
        return "taluk"
    if row.district.lower().startswith(text):
        return "district"
    return "area"


async def search_places(session: AsyncSession, raw: str) -> list[Place]:
    query = clean_query(raw)
    if query is None:
        return []
    kind, text = query
    if kind == "pincode":
        rows = (
            await session.scalars(
                select(PincodeArea)
                .where(PincodeArea.pincode.like(f"{text}%"))
                .order_by(PincodeArea.pincode, (func.lower(PincodeArea.area) != func.lower(PincodeArea.taluk)), PincodeArea.area)
                .limit(RESULT_LIMIT)
            )
        ).all()
        return [Place(**_fields(row), matched_on="pincode") for row in rows]

    area, taluk, district = func.lower(PincodeArea.area), func.lower(PincodeArea.taluk), func.lower(PincodeArea.district)
    prefix = _prefix(text)
    rank = case(
        (area == text, 0),
        (area.like(prefix, escape="\\"), 1),
        # A close spelling of a place name ("edappadi" → "Idappadi") ranks with direct matches.
        (func.similarity(area, text) >= 0.5, 1),
        (taluk == text, 2),
        (district == text, 3),
        (or_(taluk.like(prefix, escape="\\"), district.like(prefix, escape="\\")), 4),
        else_=5,
    )
    # Typo tolerance for spellings people use: "Edappadi" vs the official "Idappadi".
    similarity = func.greatest(func.similarity(area, text), func.similarity(taluk, text), func.similarity(district, text))
    rows = (
        await session.scalars(
            select(PincodeArea)
            .where(
                or_(
                    area.like(prefix, escape="\\"),
                    taluk.like(prefix, escape="\\"),
                    district.like(prefix, escape="\\"),
                    area.op("%")(text),
                    taluk.op("%")(text),
                )
            )
            # "Salem" the district beats a village named Salem elsewhere.
            .order_by(rank, case((district == text, 0), else_=1), similarity.desc(), PincodeArea.area, PincodeArea.pincode)
            .limit(RESULT_LIMIT)
        )
    ).all()
    return [Place(**_fields(row), matched_on=_matched_on(row, text)) for row in rows]


async def places_for_pincode(session: AsyncSession, pincode: str) -> list[Place]:
    """All areas under one PIN, the main town (same name as its taluk) first."""
    rows = (
        await session.scalars(
            select(PincodeArea)
            .where(PincodeArea.pincode == pincode)
            .order_by((func.lower(PincodeArea.area) != func.lower(PincodeArea.taluk)), PincodeArea.area)
        )
    ).all()
    return [Place(**_fields(row), matched_on="pincode") for row in rows]


def _fields(row: PincodeArea) -> dict:
    return {"pincode": row.pincode, "area": row.area, "taluk": row.taluk, "district": row.district, "state": row.state}
