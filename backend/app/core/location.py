"""Location helpers shared by every feature: Indian PIN code validation and "nearest first" ranking.

India Post PIN codes are hierarchical, so nearness can be ranked without maps:
all 6 digits = same post-office area, first 3 = same sorting district, first 2 = postal circle (about a state),
first digit = postal region (a group of neighbouring states).
"""
import re

from sqlalchemy import case, func, literal

PINCODE_PATTERN = re.compile(r"^[1-9][0-9]{5}$")

# Higher is nearer. A matching city counts like the same district for profiles without a PIN code.
SAME_AREA, SAME_DISTRICT, SAME_STATE, SAME_REGION, ELSEWHERE = 4, 3, 2, 1, 0


def _circles(ranges: dict[str, tuple[int, int]]) -> dict[str, str]:
    return {f"{prefix:02d}": name for name, (low, high) in ranges.items() for prefix in range(low, high + 1)}


# First two PIN digits -> India Post circle. Approximate at state borders (e.g. Goa uses 403, Puducherry 605).
STATE_BY_PREFIX = _circles({
    "Delhi": (11, 11),
    "Haryana": (12, 13),
    "Punjab & Chandigarh": (14, 16),
    "Himachal Pradesh": (17, 17),
    "Jammu & Kashmir and Ladakh": (18, 19),
    "Uttar Pradesh & Uttarakhand": (20, 28),
    "Rajasthan": (30, 34),
    "Gujarat": (36, 39),
    "Maharashtra & Goa": (40, 44),
    "Madhya Pradesh": (45, 48),
    "Chhattisgarh": (49, 49),
    "Telangana": (50, 50),
    "Andhra Pradesh": (51, 53),
    "Karnataka": (56, 59),
    "Tamil Nadu & Puducherry": (60, 66),
    "Kerala & Lakshadweep": (67, 69),
    "West Bengal, Sikkim & Andaman": (70, 74),
    "Odisha": (75, 77),
    "Assam": (78, 78),
    "North East": (79, 79),
    "Bihar & Jharkhand": (80, 85),
})


def normalize_pincode(value: str | None) -> str | None:
    """Accept '600 042' or '600042'; return None for blank, raise for anything that isn't a 6-digit Indian PIN."""
    if value is None:
        return None
    compact = re.sub(r"\s", "", str(value))
    if not compact:
        return None
    if not PINCODE_PATTERN.fullmatch(compact):
        raise ValueError("Enter a valid 6-digit PIN code")
    return compact


def same_state_prefixes(pincode: str) -> list[str]:
    """Two-digit prefixes in the same postal circle as this PIN (just its own prefix if unmapped)."""
    state = STATE_BY_PREFIX.get(pincode[:2])
    if state is None:
        return [pincode[:2]]
    return [prefix for prefix, name in STATE_BY_PREFIX.items() if name == state]


def proximity(own_pincode: str | None, own_city: str | None, near_pincode: str | None, near_city: str | None) -> int:
    """Python twin of proximity_rank, for tests and labels."""
    score = ELSEWHERE
    if near_pincode and own_pincode:
        if own_pincode == near_pincode:
            score = SAME_AREA
        elif own_pincode[:3] == near_pincode[:3]:
            score = SAME_DISTRICT
        elif own_pincode[:2] in same_state_prefixes(near_pincode):
            score = SAME_STATE
        elif own_pincode[0] == near_pincode[0]:
            score = SAME_REGION
    if near_city and own_city and own_city.strip().lower() == near_city.strip().lower():
        score = max(score, SAME_DISTRICT)
    return score


def proximity_rank(pincode_column, city_column, near_pincode: str | None, near_city: str | None):
    """SQL expression scoring each row's nearness to the searcher; None when the searcher's location is unknown."""
    parts = []
    if near_pincode:
        parts.append(
            case(
                (pincode_column == near_pincode, SAME_AREA),
                (func.substr(pincode_column, 1, 3) == near_pincode[:3], SAME_DISTRICT),
                (func.substr(pincode_column, 1, 2).in_(same_state_prefixes(near_pincode)), SAME_STATE),
                (func.substr(pincode_column, 1, 1) == near_pincode[0], SAME_REGION),
                else_=ELSEWHERE,
            )
        )
    if near_city and near_city.strip():
        parts.append(
            case((func.lower(func.trim(city_column)) == near_city.strip().lower(), SAME_DISTRICT), else_=ELSEWHERE)
        )
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else func.greatest(*parts, literal(ELSEWHERE))
