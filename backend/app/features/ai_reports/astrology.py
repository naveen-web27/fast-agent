"""Astronomical measurements; interpretations live in the service modules."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from importlib import import_module
from threading import RLock
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from .contracts import BirthInput

CALCULATION_VERSION = "1.0.0"
EPHEMERIS_LOCK = RLock()
RASI = ("Mesha", "Vrishabha", "Mithuna", "Kataka", "Simha", "Kanya",
        "Tula", "Vrischika", "Dhanus", "Makara", "Kumbha", "Meena")
NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
)
DASA_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
DASA_YEARS = (7, 20, 6, 10, 7, 18, 16, 19, 17)


def metadata(astronomical: bool = True) -> dict:
    return {
        "calculation_version": CALCULATION_VERSION,
        "ephemeris": "Swiss Ephemeris / Moshier" if astronomical else "not used",
        "zodiac": "sidereal Lahiri" if astronomical else "not applicable",
        "limitations": [
            "Traditional interpretations are cultural conventions, not scientifically established predictions.",
            "No medical, fertility, financial or marriage-outcome claims are calculated.",
        ],
    }


def swiss():
    try:
        return import_module("swisseph")
    except ImportError as exc:
        raise RuntimeError("Astronomical reports require the optional pyswisseph package") from exc


def local_to_utc(day: date, clock: time, zone: str) -> datetime:
    if clock.tzinfo is not None:
        raise ValueError("Birth time must be a naive local time")
    local = datetime.combine(day, clock)
    location = ZoneInfo(zone)
    candidates = set()
    for fold in (0, 1):
        candidate = local.replace(tzinfo=location, fold=fold).astimezone(timezone.utc)
        if candidate.astimezone(location).replace(tzinfo=None) == local:
            candidates.add(candidate)
    if len(candidates) != 1:
        raise ValueError("Ambiguous or nonexistent local time; choose an unambiguous recorded birth time")
    return candidates.pop()


def julian_day(moment: datetime) -> float:
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("An aware datetime is required")
    utc = moment.astimezone(timezone.utc)
    return (utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc)).total_seconds() / 86400 + 2451545.0


def lunar_position(longitude: float) -> dict:
    normalized = longitude % 360
    star_position = normalized * 27 / 360
    star = int(star_position)
    return {"longitude": normalized, "rasi": int(normalized / 30),
            "rasi_name": RASI[int(normalized / 30)], "nakshatra": star,
            "nakshatra_name": NAKSHATRAS[star], "pada": int((star_position - star) * 4) + 1}


def positions(moment: datetime) -> dict:
    swe = swiss()
    with EPHEMERIS_LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        result = {}
        for name, planet in (("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
                             ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER),
                             ("Venus", swe.VENUS), ("Saturn", swe.SATURN), ("Rahu", swe.MEAN_NODE)):
            values, returned = swe.calc_ut(julian_day(moment), planet, flags)
            if not returned & swe.FLG_MOSEPH:
                raise RuntimeError("Moshier ephemeris was not used")
            result[name] = {"longitude": values[0] % 360, "speed": values[3],
                            "rasi": int((values[0] % 360) / 30)}
        result["Ketu"] = {"longitude": (result["Rahu"]["longitude"] + 180) % 360,
                          "speed": result["Rahu"]["speed"], "rasi": (result["Rahu"]["rasi"] + 6) % 12}
    return result


def birth_chart(inputs: BirthInput) -> dict:
    moment = local_to_utc(inputs.birth_date, inputs.birth_time, inputs.timezone)
    planets = positions(moment)
    swe = swiss()
    with EPHEMERIS_LOCK:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        try:
            cusps, angles = swe.houses_ex(julian_day(moment), inputs.latitude,
                                         inputs.longitude, b"W", swe.FLG_SIDEREAL)
        except swe.Error as exc:
            raise ValueError("Ascendant cannot be calculated for these coordinates") from exc
    return {"metadata": metadata(), "birth": inputs.model_dump(mode="json"),
            "utc": moment.isoformat(), "planets": planets,
            "moon": lunar_position(planets["Moon"]["longitude"]),
            "ascendant": {"longitude": angles[0] % 360, "rasi": int((angles[0] % 360) / 30),
                          "house_system": "whole sign", "cusps": list(cusps)},
            "dosha": {"status": "not_calculated", "reason": "No reviewed dosha rules implemented"}}


def vimshottari(moon_longitude: float, birth: datetime, as_of: datetime) -> dict:
    if as_of < birth:
        raise ValueError("Dasa reference time cannot precede birth")
    star_position = (moon_longitude % 360) * 27 / 360
    lord_index = int(star_position) % 9
    year_days = 365.2425
    start = birth - timedelta(days=(star_position % 1) * DASA_YEARS[lord_index] * year_days)
    while True:
        end = start + timedelta(days=DASA_YEARS[lord_index] * year_days)
        if as_of < end:
            return {"lord": DASA_LORDS[lord_index], "start": start.isoformat(), "end": end.isoformat(),
                    "as_of": as_of.isoformat(), "year_days": year_days,
                    "method": "Moon-nakshatra Vimshottari mahadasa only; no antardasa",
                    "limitations": "365.2425-day year convention; other traditions use different year lengths"}
        start = end
        lord_index = (lord_index + 1) % 9


def panchangam(day: date) -> dict:
    moment = datetime.combine(day, time(12), ZoneInfo("Asia/Kolkata"))
    planets = positions(moment)
    sun = planets["Sun"]["longitude"]
    moon = planets["Moon"]["longitude"]
    elongation = (moon - sun) % 360
    half_tithi = int(elongation / 6)
    karana = ("Kimstughna" if half_tithi == 0 else
              ("Shakuni", "Chatushpada", "Naga")[half_tithi - 57] if half_tithi >= 57 else
              ("Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti")[(half_tithi - 1) % 7])
    yoga_names = ("Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
                  "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
                  "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
                  "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti")
    tithi_names = ("Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
                   "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi",
                   "Trayodashi", "Chaturdashi")
    tithi_index = int(elongation / 12)
    tithi_name = ("Purnima" if tithi_index == 14 else "Amavasya" if tithi_index == 29
                  else tithi_names[tithi_index % 15])
    yoga_index = int(((sun + moon) % 360) * 27 / 360)
    return {"date": day.isoformat(), "reference_time": moment.isoformat(),
            "reference_place": {"name": "Chennai", "latitude": 13.0827, "longitude": 80.2707},
            "tithi": {"index": tithi_index + 1, "name": tithi_name,
                      "paksha": "Shukla" if tithi_index < 15 else "Krishna"},
            "nakshatra": lunar_position(moon),
            "vara": ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[day.weekday()],
            "yoga": {"index": yoga_index + 1, "name": yoga_names[yoga_index]},
            "karana": karana, "transits": planets,
            "limitations": "Geocentric noon snapshot, not sunrise Panchangam; no transition times or muhurta computed"}