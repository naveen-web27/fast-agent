"""Sidereal (Lahiri) birth charts and Kattam checks computed with Astronomy Engine 2.1.19.

Times are milliseconds since the Unix epoch so results match the former browser engine exactly.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import astronomy as A

DAY_MS = 86_400_000
YEAR_MS = 365.2425 * DAY_MS
J2000_MS = 946_728_000_000
PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
PLANET_ORDER = PLANETS + ("Rahu", "Ketu")
SIGN_LORDS = ("Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter")
OWN_SIGNS = {"Sun": (4,), "Moon": (3,), "Mars": (0, 7), "Mercury": (2, 5),
             "Jupiter": (8, 11), "Venus": (1, 6), "Saturn": (9, 10)}
EXALTATION = {"Sun": 0, "Moon": 1, "Mars": 9, "Mercury": 5, "Jupiter": 3, "Venus": 11, "Saturn": 6}
DASA_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
DASA_YEARS = (7, 20, 6, 10, 7, 18, 16, 19, 17)
CHEVVAI_HOUSES = (2, 4, 7, 8, 12)
RAHU_KETU_HOUSES = (1, 2, 7, 8)
PAPA_PLANETS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
PAPA_HOUSES = (1, 2, 4, 7, 8, 12)
KENDRA = (1, 4, 7, 10)
TRIKONA = (1, 5, 9)
DUSTHANA = (6, 8, 12)
BENEFICS = ("Jupiter", "Venus", "Mercury")
MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
DEG = math.pi / 180


def norm(value: float) -> float:
    return ((value % 360) + 360) % 360


def house_from(from_sign: int, sign: int) -> int:
    return (sign - from_sign + 12) % 12 + 1


def nutation(t: float) -> tuple[float, float]:
    omega = (125.04452 - 1934.136261 * t) * DEG
    sun = (280.4665 + 36000.7698 * t) * DEG
    moon = (218.3165 + 481267.8813 * t) * DEG
    longitude = (-17.20 * math.sin(omega) - 1.32 * math.sin(2 * sun) - 0.23 * math.sin(2 * moon)
                 + 0.21 * math.sin(2 * omega)) / 3600
    obliquity = (9.20 * math.cos(omega) + 0.57 * math.cos(2 * sun) + 0.10 * math.cos(2 * moon)
                 - 0.09 * math.cos(2 * omega)) / 3600
    return longitude, obliquity


# Mean-equinox Lahiri ayanamsa; agrees with Swiss Ephemeris SIDM_LAHIRI to about 0.001 degree.
def ayanamsa(t: float) -> float:
    return 23.85684 + (5029.0966 * t + 1.11113 * t * t) / 3600


def tropical_longitude(body: str, time: A.Time) -> float:
    if body == "Sun":
        return A.SunPosition(time).elon
    if body == "Moon":
        return A.EclipticGeoMoon(time).lon
    return A.Ecliptic(A.GeoVector(A.Body[body], time, True)).elon


def mean_node(t: float) -> float:
    return norm(125.0445479 - 1934.1362891 * t + 0.0020754 * t * t + t ** 3 / 467441 - t ** 4 / 60616000)


def ascendant(time: A.Time, latitude: float, longitude: float, t: float) -> float:
    nut_longitude, nut_obliquity = nutation(t)
    epsilon = (23.4392911 - 0.0130042 * t + nut_obliquity) * DEG
    theta = norm(A.SiderealTime(time) * 15 + longitude) * DEG
    tropical = math.atan2(math.cos(theta), -(math.sin(theta) * math.cos(epsilon)
                                             + math.tan(latitude * DEG) * math.sin(epsilon))) / DEG
    return norm(tropical - ayanamsa(t) - nut_longitude)


def placement(longitude: float, retrograde: bool) -> dict:
    sign = math.floor(longitude / 30) % 12
    star_position = longitude * 27 / 360
    return {
        "longitude": longitude, "sign": sign, "degree": longitude - sign * 30,
        "star": math.floor(star_position) % 27,
        "pada": min(4, math.floor((star_position - math.floor(star_position)) * 4) + 1),
        "navamsa": math.floor(longitude * 3 / 10) % 12, "retrograde": retrograde,
    }


def dignity(planet: str, sign: int) -> str:
    if planet in EXALTATION:
        if EXALTATION[planet] == sign:
            return "exalted"
        if (EXALTATION[planet] + 6) % 12 == sign:
            return "debilitated"
    if sign in OWN_SIGNS.get(planet, ()):
        return "own"
    return ""


def local_to_utc(date_text: str, time_text: str, zone: str) -> int:
    local = datetime.fromisoformat(f"{date_text}T{time_text}")
    location = ZoneInfo(zone)
    candidates = set()
    for fold in (0, 1):
        candidate = local.replace(tzinfo=location, fold=fold).astimezone(timezone.utc)
        if candidate.astimezone(location).replace(tzinfo=None) == local:
            candidates.add(candidate)
    if len(candidates) != 1:
        raise ValueError("ambiguous-time" if candidates else "nonexistent-time")
    return round(candidates.pop().timestamp() * 1000)


def astro_time(utc_ms: float) -> A.Time:
    return A.Time((utc_ms - J2000_MS) / DAY_MS)


def chart_at(utc_ms: float, latitude: float, longitude: float) -> dict:
    time = astro_time(utc_ms)
    t = time.tt / 36525
    nut_longitude, _ = nutation(t)
    shift = ayanamsa(t) + nut_longitude
    planets = {}
    for body in PLANETS:
        now = norm(tropical_longitude(body, time) - shift)
        motion = ((tropical_longitude(body, time.AddDays(0.5)) - tropical_longitude(body, time.AddDays(-0.5)) + 540) % 360) - 180
        planets[body] = placement(now, body not in ("Sun", "Moon") and motion < 0)
    rahu = norm(mean_node(t) - ayanamsa(t))
    planets["Rahu"] = placement(rahu, True)
    planets["Ketu"] = placement(norm(rahu + 180), True)
    return {"utc_ms": utc_ms, "ayanamsa": shift,
            "lagna": placement(ascendant(time, latitude, longitude, t), False), "planets": planets}


def chart(birth: dict) -> dict:
    utc_ms = local_to_utc(birth["birth_date"], birth["birth_time"], birth["timezone"])
    return chart_at(utc_ms, float(birth["latitude"]), float(birth["longitude"]))


def vimshottari(moon_longitude: float, birth_ms: float) -> list[dict]:
    position = moon_longitude * 27 / 360
    first = math.floor(position) % 9
    start = birth_ms - (position - math.floor(position)) * DASA_YEARS[first] * YEAR_MS
    periods = []
    for step in range(10):
        index = (first + step) % 9
        end = start + DASA_YEARS[index] * YEAR_MS
        periods.append({"lord": DASA_LORDS[index], "index": index, "start": start, "end": end})
        start = end
    return periods


def bhuktis(period: dict) -> list[dict]:
    total = period["end"] - period["start"]
    start = period["start"]
    result = []
    for offset in range(9):
        index = (period["index"] + offset) % 9
        end = start + total * DASA_YEARS[index] / 120
        result.append({"lord": DASA_LORDS[index], "start": start, "end": end})
        start = end
    return result


def sign_of_house(lagna_sign: int, house: int) -> int:
    return (lagna_sign + house - 1) % 12


def houses_ruled(lagna_sign: int, planet: str) -> list[int]:
    return [house for house in range(1, 13) if SIGN_LORDS[sign_of_house(lagna_sign, house)] == planet]


def jupiter_supports(chart_data: dict, sign: int) -> bool:
    return any((chart_data["planets"]["Jupiter"]["sign"] + offset) % 12 == sign for offset in (0, 4, 6, 8))


def level_of(score: int) -> str:
    return "strong" if score >= 2 else "moderate" if score >= 0 else "care"


# Traditional functional-nature heuristic: trikona/lagna lords help, pure 6/8/12 lords and dusthana placement hinder.
def dasa_quality(chart_data: dict, lord: str) -> dict:
    place = chart_data["planets"][lord]
    house = house_from(chart_data["lagna"]["sign"], place["sign"])
    score = 0
    if lord in ("Rahu", "Ketu"):
        if house in (3, 6, 11):
            score += 2
        if house in (8, 12):
            score -= 2
        return {"level": "good" if score >= 2 else "challenging" if score <= -2 else "mixed", "house": house, "ruled": []}
    ruled = houses_ruled(chart_data["lagna"]["sign"], lord)
    trikona = 5 in ruled or 9 in ruled
    if trikona:
        score += 2
    if 1 in ruled:
        score += 1
    if not trikona and 1 not in ruled and any(h in DUSTHANA for h in ruled):
        score -= 2
    strength = dignity(lord, place["sign"])
    if strength in ("exalted", "own"):
        score += 1
    if strength == "debilitated":
        score -= 1
    if house in DUSTHANA:
        score -= 1
    elif house in KENDRA or house in TRIKONA:
        score += 1
    return {"level": "good" if score >= 2 else "challenging" if score <= -2 else "mixed", "house": house, "ruled": ruled}


def house_strength(chart_data: dict, house: int, malefics_help: bool = False) -> dict:
    planets = chart_data["planets"]
    sign = sign_of_house(chart_data["lagna"]["sign"], house)
    lord = SIGN_LORDS[sign]
    lord_sign = planets[lord]["sign"]
    lord_house = house_from(chart_data["lagna"]["sign"], lord_sign)
    lord_dignity = dignity(lord, lord_sign)
    occupants = [planet for planet in planets if planets[planet]["sign"] == sign]
    benefics = [planet for planet in occupants if planet in BENEFICS]
    malefics = [planet for planet in occupants if planet in MALEFICS]
    jupiter_aspect = jupiter_supports(chart_data, sign) and "Jupiter" not in occupants
    score = {"exalted": 2, "own": 1, "debilitated": -2}.get(lord_dignity, 0)
    if lord_house in DUSTHANA:
        score -= 1
    elif lord_house in KENDRA or lord_house in TRIKONA:
        score += 1
    score += len(benefics)
    score += len([p for p in malefics if p in ("Sun", "Mars")]) if malefics_help else -len(malefics)
    if jupiter_aspect:
        score += 1
    return {"house": house, "sign": sign, "lord": lord, "lord_sign": lord_sign, "lord_house": lord_house,
            "lord_dignity": lord_dignity, "occupants": occupants, "benefics": benefics, "malefics": malefics,
            "jupiter_aspect": jupiter_aspect, "score": score}


def next_period_of(periods: list[dict], lords: list[str], now_ms: float, horizon_ms: float) -> dict | None:
    minimum = 90 * DAY_MS
    for maha in periods:
        if maha["end"] - now_ms < minimum or maha["start"] > now_ms + horizon_ms:
            continue
        if maha["lord"] in lords:
            return {"maha": maha["lord"], "bhukti": None, "start": max(maha["start"], now_ms), "end": maha["end"]}
        for sub in bhuktis(maha):
            if sub["end"] - max(sub["start"], now_ms) < minimum or sub["start"] > now_ms + horizon_ms:
                continue
            if sub["lord"] in lords:
                return {"maha": maha["lord"], "bhukti": sub["lord"], "start": max(sub["start"], now_ms), "end": sub["end"]}
    return None


def life_areas(chart_data: dict, periods: list[dict], now_ms: float) -> dict:
    horizon = 20 * YEAR_MS
    career = house_strength(chart_data, 10, malefics_help=True)
    career["level"] = level_of(career["score"])
    career["period"] = next_period_of(periods, [career["lord"]], now_ms, horizon)
    health = house_strength(chart_data, 1)
    health["level"] = level_of(health["score"])
    children = house_strength(chart_data, 5)
    jupiter_sign = chart_data["planets"]["Jupiter"]["sign"]
    children["jupiter_house"] = house_from(chart_data["lagna"]["sign"], jupiter_sign)
    children["jupiter_dignity"] = dignity("Jupiter", jupiter_sign)
    if children["jupiter_dignity"] in ("exalted", "own"):
        children["score"] += 1
    if children["jupiter_dignity"] == "debilitated" or children["jupiter_house"] in DUSTHANA:
        children["score"] -= 1
    children["level"] = level_of(children["score"])
    children["period"] = next_period_of(periods, [children["lord"], "Jupiter"], now_ms, horizon)
    marriage = house_strength(chart_data, 7)
    marriage["level"] = level_of(marriage["score"])
    return {"career": career, "health": health, "children": children, "marriage": marriage}


def sidereal_sign(body: str, utc_ms: float) -> int:
    time = astro_time(utc_ms)
    t = time.tt / 36525
    return math.floor(norm(tropical_longitude(body, time) - ayanamsa(t) - nutation(t)[0]) / 30) % 12


# Marriage significators: 7th lord, Venus and 7th-house occupants (weight 2); 2nd lord, 11th lord and Jupiter (1).
def marriage_lords(chart_data: dict) -> dict[str, dict]:
    lagna, planets = chart_data["lagna"]["sign"], chart_data["planets"]
    seventh = sign_of_house(lagna, 7)
    lords: dict[str, dict] = {}

    def add(planet: str, weight: int, role: str) -> None:
        entry = lords.setdefault(planet, {"weight": 0, "roles": []})
        entry["weight"] = max(entry["weight"], weight)
        if role not in entry["roles"]:
            entry["roles"].append(role)

    add(SIGN_LORDS[seventh], 2, "seventh_lord")
    add("Venus", 2, "venus")
    for planet, place in planets.items():
        if place["sign"] == seventh:
            add(planet, 2, "in_seventh")
    add(SIGN_LORDS[sign_of_house(lagna, 2)], 1, "second_lord")
    add(SIGN_LORDS[sign_of_house(lagna, 11)], 1, "eleventh_lord")
    add("Jupiter", 1, "jupiter")
    for node in ("Rahu", "Ketu"):
        if node not in lords and lords.get(SIGN_LORDS[planets[node]["sign"]], {}).get("weight") == 2:
            add(node, 1, "node")
    return lords


def marriage_windows(chart_data: dict, periods: list[dict], now_ms: float) -> dict:
    """Months where a significator's dasa/bhukti meets Guru balam (Jupiter 2/5/7/9/11 from Moon) or Jupiter on the 7th."""
    birth = chart_data["utc_ms"]
    start = max(now_ms, birth + 21 * YEAR_MS)
    end = max(birth + 36 * YEAR_MS, start + 8 * YEAR_MS)
    lords = marriage_lords(chart_data)
    moon_sign = chart_data["planets"]["Moon"]["sign"]
    seventh = sign_of_house(chart_data["lagna"]["sign"], 7)
    subs = [dict(sub, maha=maha["lord"]) for maha in periods if maha["end"] > start and maha["start"] < end for sub in bhuktis(maha)]
    step = YEAR_MS / 12
    months = []
    at = start
    while at < end:
        sub = next((s for s in subs if s["start"] <= at < s["end"]), None)
        if sub is None:
            break
        jupiter = sidereal_sign("Jupiter", at)
        guru_house = house_from(moon_sign, jupiter)
        guru = guru_house in (2, 5, 7, 9, 11)
        on_seventh = (seventh - jupiter) % 12 in (0, 4, 6, 8)
        maha_weight = lords.get(sub["maha"], {}).get("weight", 0)
        bhukti_weight = lords.get(sub["lord"], {}).get("weight", 0)
        dasa = maha_weight + bhukti_weight
        good = bhukti_weight >= 1 and dasa >= 2 and (guru or on_seventh)
        months.append({"start": at, "end": min(at + step, end), "good": good, "strong": good and dasa >= 3 and guru,
                       "score": dasa + guru + on_seventh, "maha": sub["maha"], "bhukti": sub["lord"],
                       "guru_house": guru_house, "guru": guru, "on_seventh": on_seventh})
        at += step

    windows, current, gap = [], None, 0
    for month in months:
        if month["good"]:
            if current is None:
                current = {"start": month["start"], "months": []}
            current["months"].append(month)
            current["end"] = month["end"]
            gap = 0
        elif current is not None:
            gap += 1
            if gap > 4:
                windows.append(current)
                current, gap = None, 0
    if current is not None:
        windows.append(current)

    result = []
    for window in windows:
        good = window["months"]
        if len(good) < 3:
            continue
        peak = max(good, key=lambda m: m["score"])
        combos = list(dict.fromkeys((m["maha"], m["bhukti"]) for m in good))
        result.append({"start": window["start"], "end": window["end"], "length": len(good), "strong": sum(m["strong"] for m in good),
                       "level": "good", "combos": combos[:2], "guru_house": peak["guru_house"] if peak["guru"] else None,
                       "on_seventh": any(m["on_seventh"] for m in good), "now": window["start"] <= now_ms < window["end"]})
    if result:
        max(result, key=lambda w: (w["strong"], w["length"], -w["start"]))["level"] = "best"
    return {"windows": result, "lords": lords, "from": start, "to": end}


def joint_timeline(bride: dict, groom: dict, now_ms: float, years: int) -> list[dict]:
    horizon = now_ms + years * YEAR_MS
    boundaries = {now_ms, horizon}
    for period in bride["dasa"]["periods"] + groom["dasa"]["periods"]:
        if now_ms < period["start"] < horizon:
            boundaries.add(period["start"])
    points = sorted(boundaries)

    def covering(periods: list[dict], at: float) -> dict | None:
        return next((period for period in periods if period["start"] <= at < period["end"]), None)

    return [{"start": start, "end": points[index + 1],
             "bride": covering(bride["dasa"]["periods"], start), "groom": covering(groom["dasa"]["periods"], start)}
            for index, start in enumerate(points[:-1])]


def analyse_person(birth_chart: dict, now_ms: float) -> dict:
    lagna, planets = birth_chart["lagna"], birth_chart["planets"]
    mars = planets["Mars"]
    mars_from_lagna = house_from(lagna["sign"], mars["sign"])
    mars_from_moon = house_from(planets["Moon"]["sign"], mars["sign"])
    chevvai_raw = mars_from_lagna in CHEVVAI_HOUSES or mars_from_moon in CHEVVAI_HOUSES
    cancellations = []
    if mars["sign"] in OWN_SIGNS["Mars"]:
        cancellations.append("ownSign")
    if EXALTATION["Mars"] == mars["sign"]:
        cancellations.append("exalted")
    if planets["Jupiter"]["sign"] == mars["sign"]:
        cancellations.append("withJupiter")
    rahu_house = house_from(lagna["sign"], planets["Rahu"]["sign"])
    ketu_house = house_from(lagna["sign"], planets["Ketu"]["sign"])
    papa_hits = []
    for reference, sign in (("lagna", lagna["sign"]), ("moon", planets["Moon"]["sign"]), ("venus", planets["Venus"]["sign"])):
        for planet in PAPA_PLANETS:
            house = house_from(sign, planets[planet]["sign"])
            if house in PAPA_HOUSES:
                papa_hits.append({"reference": reference, "planet": planet, "house": house})
    seventh_sign = (lagna["sign"] + 6) % 12
    seventh_lord = SIGN_LORDS[seventh_sign]
    periods = [dict(period, quality=dasa_quality(birth_chart, period["lord"])["level"])
               for period in vimshottari(planets["Moon"]["longitude"], birth_chart["utc_ms"])]
    current = next((period for period in periods if period["start"] <= now_ms < period["end"]), None)
    current_bhukti = next((period for period in bhuktis(current) if period["start"] <= now_ms < period["end"]), None) if current else None
    upcoming = next((period for period in periods if period["start"] > now_ms), None)
    return {
        "chevvai": {"from_lagna": mars_from_lagna, "from_moon": mars_from_moon, "raw": chevvai_raw,
                    "cancellations": cancellations, "dosha": chevvai_raw and not cancellations},
        "rahu_ketu": {"rahu_house": rahu_house, "ketu_house": ketu_house,
                      "dosha": rahu_house in RAHU_KETU_HOUSES or ketu_house in RAHU_KETU_HOUSES},
        "papa": {"total": len(papa_hits), "hits": papa_hits},
        "seventh": {"sign": seventh_sign, "lord": seventh_lord, "lord_sign": planets[seventh_lord]["sign"],
                    "lord_house": house_from(lagna["sign"], planets[seventh_lord]["sign"]),
                    "lord_dignity": dignity(seventh_lord, planets[seventh_lord]["sign"]),
                    "occupants": [planet for planet in planets if planets[planet]["sign"] == seventh_sign]},
        "dasa": {"birth_lord": periods[0]["lord"], "balance_ms": periods[0]["end"] - birth_chart["utc_ms"],
                 "current": current, "current_bhukti": current_bhukti, "next": upcoming, "periods": periods},
        "life": life_areas(birth_chart, periods, now_ms),
    }


def analyse_pair(bride_chart: dict, groom_chart: dict, now_ms: float) -> dict:
    bride = analyse_person(bride_chart, now_ms)
    groom = analyse_person(groom_chart, now_ms)
    gap = (abs(bride["dasa"]["next"]["start"] - groom["dasa"]["next"]["start"])
           if bride["dasa"]["next"] and groom["dasa"]["next"] else math.inf)
    checks = [
        {"key": "chevvai", "ok": bride["chevvai"]["dosha"] == groom["chevvai"]["dosha"]},
        {"key": "rahuKetu", "ok": bride["rahu_ketu"]["dosha"] == groom["rahu_ketu"]["dosha"]},
        {"key": "papa", "ok": groom["papa"]["total"] >= bride["papa"]["total"]},
        {"key": "dasaSandhi", "ok": gap > YEAR_MS, "gap_ms": gap},
    ]
    failures = sum(not check["ok"] for check in checks)
    return {"bride": bride, "groom": groom, "checks": checks, "failures": failures,
            "level": "high" if failures == 0 else "medium" if failures == 1 else "low",
            "timeline": joint_timeline(bride, groom, now_ms, 25)}
