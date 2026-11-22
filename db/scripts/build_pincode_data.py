"""Build db/data/pincode_areas.csv.gz from India Post's All India Pincode Directory.

Source: https://data.gov.in/sites/default/files/all_india_pin_code.csv (Department of Posts, Government of India),
published under the Government Open Data License - India (GODL). Keep the attribution in docs/features/13-location.md.

Usage: python3 db/scripts/build_pincode_data.py path/to/all_india_pin_code.csv
"""
import csv
import gzip
import re
import sys
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "pincode_areas.csv.gz"

STATE_NAMES = {
    "ANDAMAN & NICOBAR ISLANDS": "Andaman & Nicobar Islands",
    "CHATTISGARH": "Chhattisgarh",
    "DADRA & NAGAR HAVELI": "Dadra & Nagar Haveli and Daman & Diu",
    "DAMAN & DIU": "Dadra & Nagar Haveli and Daman & Diu",
    "JAMMU & KASHMIR": "Jammu & Kashmir",
    "PONDICHERRY": "Puducherry",
}
# The directory predates Telangana (2014) and Ladakh (2019).
LADAKH_DISTRICTS = {"leh", "kargil", "leh (ladakh)"}
SUFFIX = re.compile(r"\s+(B\.?O|S\.?O|H\.?O|G\.?P\.?O|E\.?D\.?O|M\.?D\.?G|P\.?O)\.?$", re.IGNORECASE)


def tidy(text: str) -> str:
    text = " ".join((text or "").replace("\ufffd", "").split())
    return "" if text.upper() in ("NA", "N.A", "N.A.") else text


def title(text: str) -> str:
    return " ".join(word if word.isupper() and len(word) <= 3 else word.capitalize() for word in text.split())


def state_for(pincode: str, district: str, raw_state: str) -> str:
    if pincode.startswith("50"):
        return "Telangana"
    if district.lower() in LADAKH_DISTRICTS:
        return "Ladakh"
    raw = raw_state.strip().upper()
    return STATE_NAMES.get(raw, title(raw.lower()))


def main(source: str) -> None:
    seen: set[tuple[str, str]] = set()
    rows: list[tuple[str, str, str, str, str]] = []
    with open(source, encoding="utf-8", errors="replace", newline="") as handle:
        for record in csv.DictReader(handle):
            pincode = tidy(record["pincode"])
            if not re.fullmatch(r"[1-9][0-9]{5}", pincode):
                continue
            area = title(SUFFIX.sub("", tidy(record["officename"])))
            district = title(tidy(record["Districtname"]).lower())
            taluk = title(tidy(record["Taluk"]).lower())
            state = state_for(pincode, district, tidy(record["statename"]))
            if not area or (pincode, area.lower()) in seen:
                continue
            seen.add((pincode, area.lower()))
            rows.append((pincode, area, taluk, district, state))
    rows.sort()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(OUTPUT, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pincode", "area", "taluk", "district", "state"])
        writer.writerows(rows)
    print(f"Wrote {len(rows)} areas covering {len({row[0] for row in rows})} PIN codes to {OUTPUT}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
