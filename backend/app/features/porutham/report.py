"""Builds the compatibility reports as structured blocks and redacts the paid parts for the preview."""
from __future__ import annotations

import copy
import math
from datetime import datetime, timedelta, timezone

from app.features.ai_reports import rules as R

from . import engine as E
from .words import JATHAGAM, MONTHS, PLAIN, PORUTHAM, RASIS, STARS, WORDS

IST = timezone(timedelta(hours=5, minutes=30))
TONES = {"good": "good", "strong": "good", "no": "good", "mixed": "mixed", "moderate": "mixed", "cancelled": "mixed",
         "challenging": "care", "care": "care", "yes": "care"}
HIDDEN_HOUSES = (6, 8, 12)
WELL_PLACED_HOUSES = (1, 4, 5, 7, 9, 10)
YONI_ENEMY = {first: second for pair in R.YONI_OPPOSED for first, second in (tuple(pair), tuple(pair)[::-1])}
DEFAULT_NAMES = {"bride": "பெண்", "groom": "பையன்"}


def note(text: str, kind: str = "note") -> dict:
    return {"type": kind, "text": text}


def item(title: str, tone: str, badge: str, paragraphs: list[str], small: str | None = None) -> dict:
    return {"title": title, "tone": tone, "badge": badge, "paragraphs": [p for p in paragraphs if p], "small": small}


def items(entries: list[dict], ordered: bool = False) -> dict:
    return {"type": "items", "ordered": ordered, "items": entries}


def cell(text: str, tone: str | None = None) -> dict:
    return {"text": text, "tone": tone}


def table(head: list[str], rows: list[list], caption: str | None = None, kind: str = "") -> dict:
    return {"type": "table", "caption": caption, "kind": kind, "head": head,
            "rows": [[value if isinstance(value, dict) else cell(value) for value in row] for row in rows]}


def month(ms: float, language: str) -> str:
    moment = datetime.fromtimestamp(ms / 1000, IST)
    return f"{MONTHS[language][moment.month - 1]} {moment.year}"


def day(ms: float, language: str) -> str:
    moment = datetime.fromtimestamp(ms / 1000, IST)
    return f"{moment.day} {MONTHS[language][moment.month - 1]} {moment.year}"


def degree(value: float) -> str:
    return f"{math.floor(value)}°{math.floor((value % 1) * 60):02d}′"


# ---- Rasi / Nakshatra porutham (12 checks) ----

def stars_for_rasi(rasi: int) -> list[int]:
    return [star for star in range(27) if any((star * 4 + pada) // 9 == rasi for pada in range(4))]


def porutham_result(bride_star: int, groom_star: int, bride_rasi: int, groom_rasi: int) -> dict:
    base = R.porutham(bride_star, groom_star, bride_rasi, groom_rasi)
    count = (groom_star - bride_star) % 27 + 1
    lords = (R.SIGN_LORDS[bride_rasi], R.SIGN_LORDS[groom_rasi])
    details = {
        "dina": {"count": count, "remainder": count % 9}, "mahendra": {"count": count}, "stree_deergha": {"count": count},
        "gana": {"bride": R.GANA[bride_star], "groom": R.GANA[groom_star]},
        "yoni": {"bride": R.YONI[bride_star], "groom": R.YONI[groom_star], "enemy": YONI_ENEMY[R.YONI[bride_star]]},
        "rasi": {"sign_count": (groom_rasi - bride_rasi) % 12 + 1},
        "rasi_adhipathi": {"bride": lords[0], "groom": lords[1]},
        "vasiya": {"targets": sorted(R.VASIYA[bride_rasi])},
        "rajju": {"bride": R.RAJJU[bride_star], "groom": R.RAJJU[groom_star]},
        "vedha": {"group": next((sorted(group) for group in R.VEDHA_GROUPS if bride_star != groom_star and {bride_star, groom_star} <= group), [])},
        "nadi": {"bride": R.NADI[bride_star], "groom": R.NADI[groom_star]},
        "varna": {"bride": R.VARNA_BY_RASI[bride_rasi], "groom": R.VARNA_BY_RASI[groom_rasi]},
    }
    checks = [{"key": check["key"], "matches": check["matches_rule"], "details": details[check["key"]]} for check in base["checks"]]
    matched = base["matched_count"]
    rajju_fails = not next(check["matches"] for check in checks if check["key"] == "rajju")
    level = "high" if matched >= 9 else "medium" if matched >= 6 else "low"
    if rajju_fails and level == "high":
        level = "medium"
    return {"checks": checks, "matched": matched, "total": len(checks), "level": level, "rajju_fails": rajju_fails}


def rasi_blocks(bride: dict, groom: dict, result: dict, language: str) -> list[dict]:
    x = PORUTHAM[language]
    helpers = dict(x, rasi_list=lambda indices: ", ".join(RASIS[language][i] for i in indices),
                   star_list=lambda indices: " – ".join(STARS[language][i] for i in indices))

    def attributes(person: dict) -> dict:
        star, rasi = person["nakshatra"], person["rasi"]
        return {"rasi": RASIS[language][rasi], "star": STARS[language][star], "gana": x["gana"][R.GANA[star]],
                "yoni": x["yoni"][R.YONI[star]], "rajju": x["rajju"][R.RAJJU[star]], "nadi": x["nadi"][R.NADI[star]],
                "lord": x["lord"][R.SIGN_LORDS[rasi]]}

    first, second = attributes(bride), attributes(groom)
    blocks = [note(f"{result['matched']} / {result['total']} {x['out_of']} · {x['levels'][result['level']]}", "lead")]
    if result["rajju_fails"]:
        blocks.append({"type": "notice", "title": None, "lines": [x["rajju_warning"]]})
    blocks.append(table([x["attribute"], bride["name"], groom["name"]],
                        [[label, first[key], second[key]] for key, label in x["rows"].items()], caption=x["profile"], kind="profile"))
    blocks.append(items([item(x["names"][check["key"]], "good" if check["matches"] else "care",
                              x["matched"] if check["matches"] else x["not_matched"],
                              [x["explain"][check["key"]](check["details"], helpers)],
                              x["varna_notice"] if check["key"] == "varna" else None)
                         for check in result["checks"]], ordered=True))
    return blocks


def rasi_report(bride: dict, groom: dict, language: str) -> dict:
    result = porutham_result(bride["nakshatra"], groom["nakshatra"], bride["rasi"], groom["rasi"])
    x = PORUTHAM[language]
    return {"title": x["title"], "level": result["level"], "matched": result["matched"],
            "verdict": f"{result['matched']} / {result['total']} {x['out_of']} · {x['levels'][result['level']]}",
            "names": [bride["name"], groom["name"]],
            "blocks": rasi_blocks(bride, groom, result, language)[1:], "disclaimer": x["quick_disclaimer"]}


# ---- Kattam porutham ----

def timeline_note(p: dict, row: dict, names: dict) -> str:
    groom = row["groom"]["quality"] if row["groom"] else "mixed"
    bride = row["bride"]["quality"] if row["bride"] else "mixed"
    if groom == "good" and bride == "good":
        return p["tl"]["both_good"]
    if groom == "challenging" and bride == "challenging":
        return p["tl"]["both_hard"]
    good = names["groom"] if groom == "good" else names["bride"] if bride == "good" else None
    hard = names["groom"] if groom == "challenging" else names["bride"] if bride == "challenging" else None
    if good and hard:
        return p["tl"]["supports"](good, hard)
    if good:
        return p["tl"]["one_good"](good)
    if hard:
        return p["tl"]["one_hard"](hard, names["bride"] if hard == names["groom"] else names["groom"])
    return p["tl"]["normal"]


def life_reasons(p: dict, planet, area: str, info: dict) -> str:
    reasons = []
    if info["lord_house"] in HIDDEN_HOUSES:
        reasons.append(p["why"]["lord_hidden"](info["lord_house"]))
    elif info["lord_house"] in WELL_PLACED_HOUSES:
        reasons.append(p["why"]["lord_well"])
    if info["lord_dignity"] == "debilitated":
        reasons.append(p["why"]["lord_weak"])
    if info["benefics"]:
        reasons.append(p["why"]["benefics"](", ".join(map(planet, info["benefics"]))))
    helpers = [key for key in info["malefics"] if key in ("Sun", "Mars")] if area == "career" else []
    if helpers:
        reasons.append(p["why"]["helpers"](", ".join(map(planet, helpers))))
    if area != "career" and info["malefics"]:
        reasons.append(p["why"]["malefics"](", ".join(map(planet, info["malefics"]))))
    if info["jupiter_aspect"]:
        reasons.append(p["why"]["jupiter"])
    if area == "children":
        if info["jupiter_dignity"] == "debilitated":
            reasons.append(p["why"]["jupiter_weak"])
        elif info["jupiter_house"] in HIDDEN_HOUSES:
            reasons.append(p["why"]["jupiter_hidden"](info["jupiter_house"]))
        elif info["jupiter_dignity"]:
            reasons.append(p["why"]["jupiter_strong"])
    return p["why"]["join"](reasons) if reasons else ""


def chart_cells(chart: dict, kind: str, w: dict, language: str) -> list[dict]:
    cells = [[] for _ in range(12)]
    cells[chart["lagna"]["sign"] if kind == "rasi" else chart["lagna"]["navamsa"]].append(("Lagna", False))
    for planet, place in chart["planets"].items():
        cells[place["sign"] if kind == "rasi" else place["navamsa"]].append((planet, place["retrograde"] and planet not in ("Rahu", "Ketu")))
    retro = f"({w['retro']})"
    return [{"sign": sign, "name": RASIS[language][sign].split(" (")[0],
             "planets": " ".join(w["short"][key] + (retro if is_retro else "") for key, is_retro in occupants),
             "lagna": any(key == "Lagna" for key, _ in occupants)} for sign, occupants in enumerate(cells)]


def star_label(place: dict, language: str) -> str:
    return f"{STARS[language][place['star']]} ({place['pada']})"


def chart_block(w: dict, language: str, owners: list[tuple[dict, str]]) -> dict:
    return {"type": "charts", "charts": [
        {"title": f"{name} — {w['rasi_chart'] if kind == 'rasi' else w['navamsa_chart']}", "owner": name,
         "kind": w["rasi_chart"] if kind == "rasi" else w["navamsa_chart"], "cells": chart_cells(chart, kind, w, language)}
        for chart, name in owners for kind in ("rasi", "navamsa")]}


def planet_rows(w: dict, language: str, chart: dict) -> list[list[str]]:
    lagna = chart["lagna"]
    rows = [[w["lagna"], RASIS[language][lagna["sign"]], degree(lagna["degree"]), star_label(lagna, language), RASIS[language][lagna["navamsa"]], ""]]
    for key in E.PLANET_ORDER:
        place = chart["planets"][key]
        status = ", ".join(filter(None, [E.dignity(key, place["sign"]) and w["dignity"][E.dignity(key, place["sign"])],
                                         w["retro"] if place["retrograde"] and key not in ("Rahu", "Ketu") else ""]))
        rows.append([w["planets"][key], RASIS[language][place["sign"]], degree(place["degree"]), star_label(place, language),
                     RASIS[language][place["navamsa"]], status])
    return rows


def dosha_entries(p: dict, w: dict, person: dict) -> tuple[dict, list[dict]]:
    c, rahu_ketu = person["chevvai"], person["rahu_ketu"]
    spots = p["and"].join(p["spot"](house, ref) for ref, house in (("lagna", c["from_lagna"]), ("moon", c["from_moon"])) if house in E.CHEVVAI_HOUSES)
    chevvai = (("no", p["chevvai_no"](c)) if not c["raw"] else
               ("cancelled", p["chevvai_cancelled"](spots, ", ".join(w["cancel"][r] for r in c["cancellations"]))) if c["cancellations"] else
               ("yes", p["chevvai_yes"](spots)))
    naga = ("yes", p["naga_yes"](rahu_ketu)) if rahu_ketu["dosha"] else ("no", p["naga_no"](rahu_ketu))
    return {"chevvai": chevvai[0], "naga": naga[0]}, [
        item(p["chevvai_label"], TONES[chevvai[0]], p["state"][chevvai[0]], [chevvai[1]]),
        item(p["naga_label"], TONES[naga[0]], p["state"][naga[0]], [naga[1]])]


def dasa_entries(p: dict, planet, span, language: str, dasa: dict) -> list[dict]:
    entries = []
    if dasa["current"]:
        lord = planet(dasa["current"]["lord"])
        quality = dasa["current"]["quality"]
        entries.append(item(p["now_title"](lord), TONES[quality], p["quality"][quality], [
            p["when"](span(dasa["current"])),
            p["bhukti_now"](planet(dasa["current_bhukti"]["lord"]), month(dasa["current_bhukti"]["end"], language)) if dasa["current_bhukti"] else "",
            p["means"](lord, p["meaning"][dasa["current"]["lord"]]), p["quality_note"][quality](lord)]))
    if dasa["next"]:
        lord = planet(dasa["next"]["lord"])
        quality = dasa["next"]["quality"]
        entries.append(item(p["next_title"](lord), TONES[quality], p["quality"][quality], [
            p["when"](span(dasa["next"])), p["means"](lord, p["meaning"][dasa["next"]["lord"]]), p["quality_note"][quality](lord)]))
    return entries


def life_entries(p: dict, w: dict, planet, span, life: dict) -> list[dict]:
    entries = []
    for area in ("career", "health", "children", "marriage"):
        info = life[area]
        parts = [p["area_level"][area][info["level"]],
                 p["lord_at"](p["area_house"][area], planet(info["lord"]), info["lord_house"], info["lord_dignity"] and w["dignity"][info["lord_dignity"]])]
        if area == "career":
            parts.append(p["fields"](p["career_fields"][info["lord"]]))
        if area == "children":
            parts.append(p["jupiter_at"](info["jupiter_house"], info["jupiter_dignity"] and w["dignity"][info["jupiter_dignity"]]))
        parts.append(life_reasons(p, planet, area, info))
        if info.get("period"):
            period = info["period"]
            parts.append(p["period"][area](p["dasa_bhukti"](planet(period["maha"]), period["bhukti"] and planet(period["bhukti"])), span(period)))
        entries.append(item(p["area"][area], TONES[info["level"]], p["levels"][info["level"]], parts))
    return entries


def dasa_row(w: dict, language: str, dasa: dict, key: str) -> str:
    planet = w["planets"]
    if key == "birth":
        total = round(dasa["balance_ms"] / (E.YEAR_MS / 12))
        return f"{w['dasa_name'](planet[dasa['birth_lord']])} ({w['balance'](total // 12, total % 12)})"
    if key == "current":
        if not dasa["current"]:
            return w["none"]
        sub = dasa["current_bhukti"]
        return f"{w['dasa_name'](planet[dasa['current']['lord']])} / {w['bhukti'](planet[sub['lord']])} ({day(sub['start'], language)} – {day(sub['end'], language)})"
    return f"{w['dasa_name'](planet[dasa['next']['lord']])} — {day(dasa['next']['start'], language)}" if dasa["next"] else w["none"]


def kattam_report(people: dict, language: str, now_ms: float, selected: dict | None = None) -> dict:
    w, p = WORDS[language], PLAIN[language]
    charts = {role: E.chart(people[role]) for role in ("bride", "groom")}
    analysis = E.analyse_pair(charts["bride"], charts["groom"], now_ms)
    names = {role: people[role].get("name") or DEFAULT_NAMES[role] for role in ("bride", "groom")}
    roles = (("groom", names["groom"]), ("bride", names["bride"]))
    planet = lambda key: w["planets"][key]  # noqa: E731
    span = lambda period: f"{month(period['start'], language)} – {month(period['end'], language)}"  # noqa: E731
    moon = {role: charts[role]["planets"]["Moon"] for role in ("bride", "groom")}
    porutham = porutham_result(moon["bride"]["star"], moon["groom"]["star"], moon["bride"]["sign"], moon["groom"]["sign"])
    ranks = {"low": 0, "medium": 1, "high": 2}
    final_level = ("low", "medium", "high")[min(ranks[porutham["level"]], ranks[analysis["level"]])]
    star_name = lambda place: star_label(place, language)  # noqa: E731

    alerts, star_notes = [], []
    for role, name in roles:
        computed = moon[role]
        chosen = (selected or {}).get(role)
        if chosen:
            if chosen["nakshatra"] == computed["star"] and chosen["rasi"] == computed["sign"]:
                star_notes.append(w["star_same"](name, STARS[language][computed["star"]]))
            else:
                text = w["star_diff"](name, f"{RASIS[language][chosen['rasi']]} / {STARS[language][chosen['nakshatra']]}",
                                      f"{RASIS[language][computed['sign']]} / {STARS[language][computed['star']]}")
                star_notes.append(text)
                alerts.append(text)
        else:
            star_notes.append(w["star_computed"](name, STARS[language][computed["star"]]))
        fraction = (computed["longitude"] * 27 / 360) % 1
        edges = []
        if fraction < 0.02 or fraction > 0.98:
            edges.append(w["edge_moon"](name))
        if charts[role]["lagna"]["degree"] < 1 or charts[role]["lagna"]["degree"] > 29:
            edges.append(w["edge_lagna"](name))
        star_notes += edges
        alerts += edges
    star_notes.append(w["porutham_score"](porutham["matched"], w["porutham_levels"][porutham["level"]]))

    sections = []

    def section(key: str, part: str, blocks: list[dict], title: str | None = None) -> None:
        sections.append({"key": key, "part": part, "title": title or p["sections"][key], "blocks": blocks, "banner": key == "rasi"})

    rasi_people = {role: {"name": names[role], "rasi": moon[role]["sign"], "nakshatra": moon[role]["star"]} for role in ("bride", "groom")}
    section("rasi", "rasi", [note(PORUTHAM[language]["from_birth"], "help")] + rasi_blocks(rasi_people["bride"], rasi_people["groom"], porutham, language),
            title=w["parts"]["rasi"])

    blocks = [note(p["chevvai_what"]), note(p["naga_what"])]
    states = {}
    for role, name in roles:
        states[role], entries = dosha_entries(p, w, analysis[role])
        blocks += [note(name, "person"), items(entries)]
    section("dosha", "kattam", blocks)

    together = []
    for check in analysis["checks"]:
        if check["key"] in ("chevvai", "rahuKetu"):
            key = "chevvai" if check["key"] == "chevvai" else "naga"
            label = p["chevvai_label"] if key == "chevvai" else p["naga_label"]
            has = [name for role, name in roles if states[role][key] == "yes"]
            text = p["both"](label) if len(has) == 2 else p["neither"](label) if not has else p["only_one"](label, has[0])
        elif check["key"] == "papa":
            text = p["papa"](analysis["groom"]["papa"]["total"], analysis["bride"]["papa"]["total"], names["groom"], names["bride"], check["ok"])
        else:
            def label(role: str) -> str:
                upcoming = analysis[role]["dasa"]["next"]
                return p["sandhi_person"](names[role], planet(upcoming["lord"]), month(upcoming["start"], language)) if upcoming else f"{names[role]}: —"
            gap = round(check["gap_ms"] / (E.YEAR_MS / 12)) if math.isfinite(check["gap_ms"]) else "—"
            text = p["sandhi"](label("groom"), label("bride"), gap, check["ok"])
        badge = w["ok"] if check["ok"] else p["care_word"] if check["key"] == "dasaSandhi" else w["not_ok"]
        together.append(item(p["check_title"][check["key"]], "good" if check["ok"] else "care", badge, [text]))
    section("together", "kattam", [items(together)])

    blocks = []
    for role, name in roles:
        blocks += [note(name, "person"), items(dasa_entries(p, planet, span, language, analysis[role]["dasa"]))]
    section("dasa", "kattam", blocks)

    def dasa_cell(period: dict | None) -> dict:
        return cell(f"{planet(period['lord'])} — {p['quality'][period['quality']]}", TONES[period["quality"]]) if period else cell("—")

    rows = [[span(row), dasa_cell(row["groom"]), dasa_cell(row["bride"]), timeline_note(p, row, names)] for row in analysis["timeline"]]
    section("timeline", "kattam", [note(p["timeline_intro"]), table(p["tl_head"](names["groom"], names["bride"]), rows, kind="timeline")])

    blocks = []
    for role, name in roles:
        blocks += [note(name, "person"), items(life_entries(p, w, planet, span, analysis[role]["life"]))]
    blocks.append(note(p["care_note"], "help"))
    section("life", "kattam", blocks)

    checks = []
    months = lambda ms: round(ms / (E.YEAR_MS / 12))  # noqa: E731
    for check in analysis["checks"]:
        parts = []
        if check["key"] == "chevvai":
            for role, name in roles:
                parts.append(f"{name}: {w['chevvai_person'](analysis[role]['chevvai'], w)}")
            parts.append(w["chevvai_rule"])
        elif check["key"] == "rahuKetu":
            for role, name in roles:
                parts.append(f"{name}: {w['rahu_person'](analysis[role]['rahu_ketu'], w)}")
            parts.append(w["rahu_rule"])
        elif check["key"] == "papa":
            parts.append(w["papa_rule"](analysis["bride"]["papa"]["total"], analysis["groom"]["papa"]["total"]))
            for role, name in roles:
                grouped = []
                for reference, label in w["papa_refs"].items():
                    hits = [f"{planet(hit['planet'])} ({hit['house']})" for hit in analysis[role]["papa"]["hits"] if hit["reference"] == reference]
                    grouped.append(f"{label}: {', '.join(hits) if hits else w['none']}")
                parts.append(f"{name} — {'; '.join(grouped)}")
        else:
            def label(role: str) -> str:
                upcoming = analysis[role]["dasa"]["next"]
                return f"{w['dasa_name'](planet(upcoming['lord']))} {day(upcoming['start'], language)}" if upcoming else w["none"]
            parts.append(w["dasa_rule"](label("bride"), label("groom"), months(check["gap_ms"]) if math.isfinite(check["gap_ms"]) else "—"))
        checks.append(item(w["checks"][check["key"]], "good" if check["ok"] else "care", w["ok"] if check["ok"] else w["not_ok"], parts))
    section("checks", "kattam", [items(checks, ordered=True)])

    summary = [p["summary_stars"](porutham["matched"], w["porutham_levels"][porutham["level"]]),
               *[(w["summary_ok"] if check["ok"] else w["summary_bad"])[check["key"]] for check in analysis["checks"]],
               p["summary_now"](timeline_note(p, analysis["timeline"][0], names)) if analysis["timeline"] else "",
               w["final"][final_level]]
    section("summary", "kattam", [{"type": "summary", "level": final_level, "lines": [line for line in summary if line]}])

    blocks = [note(w["sections"]["birth"], "subheading")]
    birth_rows = [
        [w["rows"]["date"], *[people[role]["birth_date"] for role, _ in roles]],
        [w["rows"]["time"], *[people[role]["birth_time"] for role, _ in roles]],
        [w["rows"]["place"], *[people[role].get("place") or "—" for role, _ in roles]],
        [w["rows"]["coordinates"], *[f"{people[role]['latitude']}, {people[role]['longitude']}" for role, _ in roles]],
        [w["rows"]["timezone"], *[people[role]["timezone"] for role, _ in roles]],
        [w["rows"]["lagna"], *[f"{RASIS[language][charts[role]['lagna']['sign']]} {degree(charts[role]['lagna']['degree'])}" for role, _ in roles]],
        [w["rows"]["rasi"], *[RASIS[language][moon[role]["sign"]] for role, _ in roles]],
        [w["rows"]["star"], *[star_name(moon[role]) for role, _ in roles]],
        [w["rows"]["ayanamsa"], *[degree(charts[role]["ayanamsa"]) for role, _ in roles]],
    ]
    blocks.append(table(["", names["groom"], names["bride"]], birth_rows))
    blocks.append(note(w["sections"]["charts"], "subheading"))
    blocks.append(chart_block(w, language, [(charts[role], name) for role, name in roles]))
    blocks.append(note(w["sections"]["planets"], "subheading"))
    for role, name in roles:
        blocks.append(table(list(w["planet_head"]), planet_rows(w, language, charts[role]), caption=name))
    blocks.append(note(w["sections"]["seventh"], "subheading"))
    blocks += [note(f"{name}: {w['seventh'](analysis[role]['seventh'], w, RASIS[language])}") for role, name in roles]
    blocks.append(note(w["sections"]["dasa"], "subheading"))
    blocks.append(table(["", names["groom"], names["bride"]],
                        [[label, *[dasa_row(w, language, analysis[role]["dasa"], key) for role, _ in roles]] for key, label in w["dasa_rows"].items()]))
    blocks.append(note(w["sections"]["star"], "subheading"))
    blocks += [note(text) for text in star_notes]
    blocks += [note(w["sections"]["method"], "subheading"), note(w["method"], "help")]
    section("expert", "expert", blocks)

    return {
        "kind": "kattam", "title": w["title"], "names": names, "parts": w["parts"],
        "subtitle": f"{names['groom']} · {names['bride']}",
        "score": {"stars": porutham["matched"], "kattam": 4 - analysis["failures"]},
        "verdict": {"level": final_level, "headline": p["verdict"][final_level],
                    "detail": f"{p['verdict_detail'](porutham['matched'], 4 - analysis['failures'])} · {names['groom']} · {names['bride']}"},
        "alerts": {"title": p["star_alert"], "lines": alerts} if alerts else None,
        "sections": sections, "disclaimer": w["disclaimer"], "locked": False,
    }


# ---- Individual Jathagam ----

QUALITY_LEVEL = {"good": "high", "mixed": "medium", "challenging": "low"}


def jathagam_report(person: dict, language: str, now_ms: float) -> dict:
    w, p, j = WORDS[language], PLAIN[language], JATHAGAM[language]
    chart = E.chart(person)
    analysis = E.analyse_person(chart, now_ms)
    name = person.get("name") or j["default_name"]
    planet = lambda key: w["planets"][key]  # noqa: E731
    span = lambda period: f"{month(period['start'], language)} – {month(period['end'], language)}"  # noqa: E731
    moon, lagna = chart["planets"]["Moon"], chart["lagna"]
    names = (RASIS[language][lagna["sign"]], RASIS[language][moon["sign"]], star_label(moon, language))
    dasa = analysis["dasa"]
    current_quality = dasa["current"]["quality"] if dasa["current"] else "mixed"
    sections = []

    def section(key: str, part: str, blocks: list[dict], banner: bool = False) -> None:
        sections.append({"key": key, "part": part, "title": j["parts"][part] if banner else j["sections"][key], "blocks": blocks, "banner": banner})

    alerts = []
    fraction = (moon["longitude"] * 27 / 360) % 1
    if fraction < 0.02 or fraction > 0.98:
        alerts.append(w["edge_moon"](name))
    if lagna["degree"] < 1 or lagna["degree"] > 29:
        alerts.append(w["edge_lagna"](name))

    section("basic", "chart", [table(["", name], [
        [w["rows"]["date"], person["birth_date"]], [w["rows"]["time"], person["birth_time"]], [w["rows"]["place"], person.get("place") or "—"],
        [w["rows"]["lagna"], f"{names[0]} {degree(lagna['degree'])}"], [w["rows"]["rasi"], names[1]], [w["rows"]["star"], names[2]],
        [w["rows"]["ayanamsa"], degree(chart["ayanamsa"])]])], banner=True)
    section("charts", "chart", [chart_block(w, language, [(chart, name)])])
    states, entries = dosha_entries(p, w, analysis)
    section("dosha", "palan", [note(p["chevvai_what"]), note(p["naga_what"]), items(entries)])
    section("planets", "palan", [table(list(w["planet_head"]), planet_rows(w, language, chart))])
    section("dasa", "palan", [items(dasa_entries(p, planet, span, language, dasa))])

    horizon = now_ms + 25 * E.YEAR_MS
    rows = [[span({"start": max(period["start"], now_ms), "end": min(period["end"], horizon)}), w["dasa_name"](planet(period["lord"])),
             cell(p["quality"][period["quality"]], TONES[period["quality"]]), p["meaning"][period["lord"]]]
            for period in dasa["periods"] if period["end"] > now_ms and period["start"] < horizon]
    section("timeline", "palan", [note(j["timeline_intro"]), table(j["tl_head"], rows, kind="timeline")])
    section("life", "palan", [items(life_entries(p, w, planet, span, analysis["life"])), note(p["care_note"], "help")])

    if dasa["current"]:
        bhukti_rows = []
        for sub in E.bhuktis(dasa["current"]):
            quality = E.dasa_quality(chart, sub["lord"])["level"]
            now = j["now"] if sub["start"] <= now_ms < sub["end"] else ""
            bhukti_rows.append([span(sub), f"{w['bhukti'](planet(sub['lord']))}{now}", cell(p["quality"][quality], TONES[quality])])
        section("bhukti", "palan", [note(j["bhukti_intro"](planet(dasa["current"]["lord"]))), table(j["bhukti_head"], bhukti_rows, kind="timeline")])

    area_names = p["area"]
    strong = [area_names[area] for area, info in analysis["life"].items() if info["level"] == "strong"]
    care = [area_names[area] for area, info in analysis["life"].items() if info["level"] == "care"]
    summary = [j["summary_chart"](*names), j["summary_dosha"](p["state"][states["chevvai"]], p["state"][states["naga"]])]
    if dasa["current"]:
        summary.append(j["summary_now"](w["dasa_name"](planet(dasa["current"]["lord"])), p["quality"][current_quality], month(dasa["current"]["end"], language)))
    if dasa["next"]:
        summary.append(j["summary_next"](w["dasa_name"](planet(dasa["next"]["lord"])), month(dasa["next"]["start"], language), p["quality"][dasa["next"]["quality"]]))
    if strong:
        summary.append(j["summary_strong"](", ".join(strong)))
    if care:
        summary.append(j["summary_care"](", ".join(care)))
    summary.append(j["final"][current_quality])
    section("summary", "palan", [{"type": "summary", "level": QUALITY_LEVEL[current_quality], "lines": summary}])

    section("expert", "palan", [
        note(w["sections"]["seventh"], "subheading"), note(w["seventh"](analysis["seventh"], w, RASIS[language])),
        note(w["sections"]["dasa"], "subheading"),
        table(["", name], [[label, dasa_row(w, language, dasa, key)] for key, label in w["dasa_rows"].items()]),
        note(w["sections"]["method"], "subheading"), note(w["method"], "help")])

    return {
        "kind": "jathagam", "title": j["title"], "names": {"person": name}, "parts": j["parts"], "subtitle": name,
        "score": {"stars": 0, "kattam": 0, "period": current_quality},
        "verdict": {"level": QUALITY_LEVEL[current_quality], "headline": j["headline"](*names),
                    "detail": f"{name} · {person['birth_date']} {person['birth_time'][:5]} · {person.get('place') or '—'}"},
        "alerts": {"title": p["star_alert"], "lines": alerts} if alerts else None,
        "sections": sections, "disclaimer": j["disclaimer"], "locked": False,
    }


# ---- Preview redaction: paid text never leaves the server before payment ----

def hidden(text: str) -> int:
    return max(12, len(text))


def hide_item(entry: dict, keep_title: bool = True, keep_lines: int = 0) -> dict:
    return {"title": entry["title"] if keep_title else None, "badge": entry["badge"] if keep_title else None,
            "tone": entry["tone"] if keep_title else "locked", "paragraphs": entry["paragraphs"][:keep_lines],
            "hidden": [hidden(text) for text in entry["paragraphs"][keep_lines:]] + ([hidden(entry["small"])] if entry.get("small") else []),
            "small": None}


def hide_block(block: dict) -> dict:
    kind = block["type"]
    if kind in ("note", "help", "lead"):
        return {"type": kind, "hidden": [hidden(block["text"])]}
    if kind == "items":
        return dict(block, items=[hide_item(entry, keep_title=False) for entry in block["items"]])
    if kind == "table":
        return dict(block, rows=[[{"hidden": hidden(value["text"])} for value in row] for row in block["rows"]])
    if kind == "summary":
        return {"type": "summary", "level": block["level"], "lines": [], "hidden": [hidden(line) for line in block["lines"]]}
    if kind == "charts":
        return {"type": "charts", "charts": [{"title": chart["title"], "cells": None} for chart in block["charts"]]}
    return block


# What a reader sees before paying, per section: free, titles (headings + badges), rows (two rows, then only
# the period of the last three), one_line (heading + first sentence), first_two (two rows open), hidden.
POLICIES = {
    "kattam": {"rasi": "free", "dosha": "free", "together": "titles", "dasa": "titles", "timeline": "rows",
               "life": "one_line", "checks": "first_two", "summary": "hidden", "expert": "hidden"},
    "jathagam": {"basic": "free", "charts": "free", "dosha": "titles", "planets": "rows", "dasa": "titles", "timeline": "rows",
                 "life": "one_line", "bhukti": "rows", "summary": "hidden", "expert": "hidden"},
}


def redact(block: dict, policy: str) -> dict:
    kind = block["type"]
    if kind in ("person", "subheading") or (kind in ("note", "help") and policy != "hidden"):
        return block
    if kind == "items" and policy == "titles":
        return dict(block, items=[hide_item(entry) for entry in block["items"]])
    if kind == "items" and policy == "one_line":
        return dict(block, items=[hide_item(entry, keep_lines=1) for entry in block["items"]])
    if kind == "items" and policy == "first_two":
        return dict(block, items=block["items"][:2] + [hide_item(entry, keep_title=False) for entry in block["items"][2:]])
    if kind == "table" and policy == "rows":
        rows = block["rows"]
        tail = max(2, len(rows) - 3)
        return dict(block, rows=rows[:2] + [[value if index == 0 and position >= tail else {"hidden": hidden(value["text"])}
                                              for index, value in enumerate(row)] for position, row in enumerate(rows[2:], start=2)])
    if kind == "table":
        return dict(hide_block(block), caption=block["caption"])
    return hide_block(block)


def preview(report: dict, language: str) -> dict:
    result = copy.deepcopy(report)
    kind = result.get("kind", "kattam")
    policies = POLICIES[kind]
    teaser = JATHAGAM[language]["teaser"] if kind == "jathagam" else PLAIN[language]["teaser"]
    for section in result["sections"]:
        policy = policies[section["key"]]
        if policy == "free":
            result["paywall_after"] = section["key"]
            continue
        section["teaser"] = teaser.get(section["key"])
        section["blocks"] = [redact(block, policy) for block in section["blocks"]]
    result["locked"] = True
    return result
