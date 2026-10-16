"""No database, AI credentials or downloaded ephemeris files are needed."""
import asyncio
import importlib.util
import json
import subprocess
import sys
import types
import unittest
from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

from app.features.ai_reports import astrology, rules

HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None
if HAS_PYDANTIC:
    from pydantic import ValidationError

    from app.features.ai_reports.contracts import BirthInput, StrictInput, WrittenReport
    from app.features.ai_reports.modules.baby_names import BabyNamesInput
    from app.features.ai_reports.modules.compatibility import CompatibilityInput
    from app.features.ai_reports.modules.forecast import ForecastInput
    from app.features.ai_reports.modules.numerology import NumerologyInput
    from app.features.ai_reports.modules.vastu import VastuInput
    from app.features.ai_reports.registry import SERVICES, get_service

BIRTH = {"name": "Arul", "birth_date": "2000-01-01", "birth_time": "17:30",
         "place": "Chennai", "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata"}
HAS_SWISS = importlib.util.find_spec("swisseph") is not None


@unittest.skipUnless(HAS_PYDANTIC, "Pydantic is not installed; service/schema checks require it")
class SchemaTests(unittest.TestCase):
    def test_all_seven_services_have_independent_metadata_and_schemas(self):
        self.assertEqual(set(SERVICES), {"horoscope", "numerology", "compatibility", "vastu", "gemstone", "baby-names", "forecast"})
        for key, service in SERVICES.items():
            with self.subTest(key=key):
                self.assertIs(get_service(key), service)
                self.assertEqual(service.key, key)
                self.assertTrue(issubclass(service.input_schema, StrictInput))
                for field in ("title_ta", "title_en", "description_ta", "description_en", "icon"):
                    self.assertTrue(getattr(service, field))
                self.assertIsInstance(service.sections, tuple)
                self.assertEqual(len(service.sections), len(set(service.sections)))
                self.assertGreaterEqual(len(service.sections), 3)
                self.assertLessEqual(len(service.sections), 12)
                self.assertTrue(all(section.isascii() for section in service.sections))
                self.assertFalse(service.input_schema.model_json_schema()["additionalProperties"])
        with self.assertRaises(KeyError):
            get_service("unknown")

    def test_exact_frontend_field_names(self):
        for key in ("horoscope", "gemstone"):
            self.assertIs(SERVICES[key].input_schema, BirthInput)
        expected = {"numerology": {"full_name", "birth_date"}, "compatibility": {"bride", "groom"},
                    "vastu": {"facing", "main_door", "kitchen", "bedroom"},
                    "forecast": {"rasi", "period"}, "baby-names": set(BirthInput.model_fields) | {"gender"}}
        for key, fields in expected.items():
            self.assertEqual(set(SERVICES[key].input_schema.model_fields), fields)
        self.assertIsInstance(CompatibilityInput(bride=BIRTH, groom=BIRTH).bride, BirthInput)
        self.assertEqual(BabyNamesInput(**BIRTH).gender, "neutral")

    def test_invalid_birth_and_form_values(self):
        for invalid in ({"birth_date": "1899-12-31"}, {"birth_date": (date.today() + timedelta(days=1)).isoformat()},
                        {"timezone": "Not/A_Zone"}, {"latitude": 91}, {"longitude": -181},
                        {"birth_time": "12:00+05:30"}, {"latitude": float("nan")}):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                BirthInput(**(BIRTH | invalid))
        for rasi in (-1, 12, 1.5, True, "1"):
            with self.subTest(rasi=rasi), self.assertRaises(ValidationError):
                ForecastInput(rasi=rasi)
        with self.assertRaises(ValidationError):
            ForecastInput(rasi=0, period="monthly")
        for gender in ("boy", "girl", "other"):
            with self.assertRaises(ValidationError):
                BabyNamesInput(**BIRTH, gender=gender)
        with self.assertRaises(ValidationError):
            VastuInput(facing="north", main_door="E", kitchen="SE", bedroom="SW")
        with self.assertRaises(ValidationError):
            NumerologyInput(full_name="Arul", birth_date="2000-01-01", extra="ignored")

    def test_importing_registry_does_not_import_optional_clients(self):
        code = ("import sys; from app.features.ai_reports.registry import SERVICES; "
                "assert 'swisseph' not in sys.modules; assert 'app.features.ai_reports.writer' not in sys.modules")
        subprocess.run([sys.executable, "-c", code], check=True, capture_output=True)

    def test_writer_delegation_for_each_module_and_language(self):
        expected = WrittenReport(title="Report", sections=[{"heading": "Context", "body": "Text"}], disclaimer="Cultural context only")
        helper = types.ModuleType("app.features.ai_reports.writer")
        helper.write_report = AsyncMock(return_value=expected)
        with patch.dict(sys.modules, {"app.features.ai_reports.writer": helper}):
            for key, service in SERVICES.items():
                for language in ("ta", "en"):
                    raw = {"service": key}
                    result = asyncio.run(service.generate_report(raw, language))
                    self.assertIs(result, expected)
                    helper.write_report.assert_awaited_with(key, service.sections, raw, language)
                asyncio.run(service.generate_report({}))
                helper.write_report.assert_awaited_with(key, service.sections, {}, "ta")


class ArithmeticTests(unittest.TestCase):
    def test_j2000_and_timezone_fixtures(self):
        utc = astrology.local_to_utc(date(2000, 1, 1), time(17, 30), "Asia/Kolkata")
        self.assertEqual(utc, datetime(2000, 1, 1, 12, tzinfo=timezone.utc))
        self.assertEqual(astrology.julian_day(utc), 2451545.0)
        self.assertEqual(astrology.julian_day(utc.astimezone(ZoneInfo("America/New_York"))), 2451545.0)
        with self.assertRaises(ValueError):
            astrology.julian_day(datetime(2000, 1, 1))

    def test_dst_gaps_and_folds_are_rejected(self):
        for day, clock, zone in ((date(2024, 3, 10), time(2, 30), "America/New_York"),
                                 (date(2024, 11, 3), time(1, 30), "America/New_York"),
                                 (date(2024, 10, 6), time(2, 15), "Australia/Lord_Howe"),
                                 (date(2011, 12, 30), time(12), "Pacific/Apia")):
            with self.subTest(day=day, zone=zone), self.assertRaisesRegex(ValueError, "Ambiguous or nonexistent"):
                astrology.local_to_utc(day, clock, zone)
        self.assertEqual(astrology.local_to_utc(date(2024, 11, 3), time(3), "America/New_York").hour, 8)
        with self.assertRaises(ValueError):
            astrology.local_to_utc(date(2000, 1, 1), time(12, tzinfo=timezone.utc), "UTC")

    def test_moon_divisions_at_boundaries(self):
        expected = ((0, 0, 0, 1), (10, 0, 0, 4), (30, 1, 2, 2),
                    (180, 6, 13, 3), (359.999, 11, 26, 4), (360, 0, 0, 1))
        for longitude, rasi, star, pada in expected:
            result = astrology.lunar_position(longitude)
            self.assertEqual((result["rasi"], result["nakshatra"], result["pada"]), (rasi, star, pada))

    @unittest.skipUnless(HAS_PYDANTIC, "Pydantic is not installed")
    def test_pythagorean_known_name_and_date(self):
        result = SERVICES["numerology"].calculate(NumerologyInput(full_name="John Smith", birth_date="1990-01-01"))
        self.assertEqual(result["name_total"], 44)
        self.assertEqual(result["name_number"], 8)
        self.assertEqual(result["life_path_total"], 21)
        self.assertEqual(result["life_path_number"], 3)
        self.assertEqual(result["birth_number"], 1)
        self.assertEqual(result["metadata"]["ephemeris"], "not used")
        for number, reduced in ((11, 11), (22, 22), (33, 33), (29, 11), (99, 9), (0, 0), (1234, 1)):
            self.assertEqual(rules.reduce_number(number), reduced)
        for invalid in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                rules.reduce_number(invalid)

    @unittest.skipUnless(HAS_PYDANTIC, "Pydantic is not installed")
    def test_names_require_english_actual_spelling(self):
        for full_name in ("தமிழ்", "José", " ", "Unknown", "Not Provided", "Name", "A", "Arul1", "N/A"):
            with self.subTest(full_name=full_name), self.assertRaises(ValidationError):
                NumerologyInput(full_name=full_name, birth_date="2000-01-01")
        self.assertEqual(NumerologyInput(full_name="  Arul   Mani ", birth_date="2000-01-01").full_name, "Arul Mani")

    def test_vimshottari_balance_and_period_boundary(self):
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
        result = astrology.vimshottari(0, birth, birth)
        self.assertEqual(result["lord"], "Ketu")
        boundary = birth + timedelta(days=7 * 365.2425)
        self.assertEqual(datetime.fromisoformat(result["end"]), boundary)
        self.assertEqual(astrology.vimshottari(0, birth, boundary)["lord"], "Venus")
        half = astrology.vimshottari(360 / 54, birth, birth)
        self.assertEqual(datetime.fromisoformat(half["start"]), birth - timedelta(days=3.5 * 365.2425))
        self.assertEqual(astrology.vimshottari(0, birth, birth + timedelta(days=120 * 365.2425))["lord"], "Ketu")
        with self.assertRaises(ValueError):
            astrology.vimshottari(0, birth, birth - timedelta(seconds=1))

    def test_all_twelve_porutham_outcomes_and_count_fixture(self):
        result = rules.porutham(0, 13, 0, 6)
        outcomes = {check["key"]: check["matches_rule"] for check in result["checks"]}
        self.assertEqual(outcomes, {"dina": False, "gana": False, "mahendra": False,
                                  "stree_deergha": True, "yoni": True, "rasi": True,
                                  "rasi_adhipathi": False, "vasiya": False, "rajju": True,
                                  "vedha": True, "nadi": True, "varna": False})
        self.assertEqual(result["matched_count"], 6)
        self.assertEqual(result["total_checks"], 12)
        self.assertEqual([check["key"] for check in result["checks"]],
                 ["dina", "gana", "mahendra", "stree_deergha", "yoni", "rasi",
                  "rasi_adhipathi", "vasiya", "rajju", "vedha", "nadi", "varna"])
        self.assertTrue(all(check["name_ta"] and check["name_en"] for check in result["checks"]))
        self.assertIn("caste-coded", next(check for check in result["checks"] if check["key"] == "varna")["details"]["rule"])
        self.assertEqual(result["review_status"], "unreviewed")
        self.assertTrue(result["sources"])
        self.assertTrue(any("probability" in limit for limit in result["limitations"]))
        same = rules.porutham(0, 0, 0, 0)
        self.assertFalse(next(check for check in same["checks"] if check["key"] == "rajju")["matches_rule"])
        opposed = rules.porutham(0, 17, 0, 7)
        self.assertFalse(next(check for check in opposed["checks"] if check["key"] == "vedha")["matches_rule"])

    def test_porutham_tables_cover_all_stars_and_all_pairs_are_total(self):
        self.assertEqual(len(rules.GANA), 27)
        self.assertEqual(len(rules.YONI), 27)
        self.assertEqual(len(rules.RAJJU), 27)
        self.assertEqual(set().union(*rules.VEDHA_GROUPS), set(range(27)))
        for bride_star in range(27):
            for groom_star in range(27):
                result = rules.porutham(bride_star, groom_star, bride_star % 12, groom_star % 12)
                self.assertEqual(len(result["checks"]), 12)
                self.assertEqual(result["matched_count"], sum(check["matches_rule"] for check in result["checks"]))
        with self.assertRaises(ValueError):
            rules.porutham(-1, 0, 0, 0)

    def test_curated_names_have_validated_explicit_prefix_and_meaning(self):
        self.assertEqual(len(rules.NAMING_SYLLABLES), 27)
        self.assertTrue(all(len(syllables) == 4 for syllables in rules.NAMING_SYLLABLES))
        for entry in rules.BABY_NAMES:
            self.assertTrue(rules.name_matches(entry, entry["syllable"]))
            self.assertTrue(entry["meaning_ta"])
            self.assertTrue(entry["meaning_en"])
            self.assertTrue(entry["lexeme"])
        options = rules.baby_name_options(2, 1, "neutral")
        self.assertEqual([entry["name_en"] for entry in options["names"]], ["Arul", "Anbu"])
        self.assertTrue(all(entry["meaning_source"] == rules.NAME_LEXICON for entry in options["names"]))
        empty = rules.baby_name_options(0, 1, "neutral")
        self.assertEqual(empty["names"], [])
        self.assertEqual(empty["coverage"], "no_curated_matches")
        self.assertEqual(rules.baby_name_options(2, 2, "female")["names"], [])
        for args in ((27, 1, "neutral"), (0, 0, "neutral"), (0, 1, "invalid")):
            with self.assertRaises(ValueError):
                rules.baby_name_options(*args)

    @unittest.skipUnless(HAS_PYDANTIC, "Pydantic is not installed")
    def test_vastu_all_fields_and_no_remedy_inference(self):
        result = SERVICES["vastu"].calculate(VastuInput(facing="N", main_door="E", kitchen="SE", bedroom="SW"))
        self.assertEqual(len(result["checks"]), 4)
        self.assertTrue(all(check["traditional_preference"] for check in result["checks"]))
        self.assertTrue(any("demolition" in value for value in result["limitations"]))
        json.dumps(result)

    def test_missing_ephemeris_is_explicit_not_fabricated(self):
        with patch.object(astrology, "import_module", side_effect=ImportError):
            with self.assertRaisesRegex(RuntimeError, "optional pyswisseph"):
                astrology.positions(datetime(2000, 1, 1, tzinfo=timezone.utc))

    def test_locked_explicit_ephemeris_flags_without_optional_package(self):
        calls = []

        def set_mode(mode):
            self.assertTrue(astrology.EPHEMERIS_LOCK._is_owned())
            self.assertEqual(mode, 1)

        def calculate_planet(julian_day, planet, flags):
            self.assertTrue(astrology.EPHEMERIS_LOCK._is_owned())
            self.assertEqual(julian_day, 2451545.0)
            self.assertEqual(flags, 4 | 65536 | 256)
            calls.append(planet)
            return ((planet * 30.0, 0, 1, 0.5, 0, 0), flags)

        backend = types.SimpleNamespace(SIDM_LAHIRI=1, FLG_MOSEPH=4, FLG_SIDEREAL=65536, FLG_SPEED=256,
                                        SUN=0, MOON=1, MARS=4, MERCURY=2, JUPITER=5, VENUS=3,
                                        SATURN=6, MEAN_NODE=10, set_sid_mode=set_mode, calc_ut=calculate_planet)
        moment = datetime(2000, 1, 1, 12, tzinfo=timezone.utc)
        with patch.object(astrology, "swiss", return_value=backend):
            result = astrology.positions(moment)
            self.assertEqual(len(calls), 8)
            self.assertEqual(len(result), 9)
            self.assertEqual(result["Ketu"]["longitude"], 120)
            self.assertEqual(result["Ketu"]["rasi"], 4)
            backend.calc_ut = lambda *args: ((0, 0, 0, 0, 0, 0), 65536)
            with self.assertRaisesRegex(RuntimeError, "Moshier ephemeris was not used"):
                astrology.positions(moment)

    def test_master_number_reduction_without_schema_dependency(self):
        for number, reduced in ((11, 11), (22, 22), (33, 33), (29, 11), (99, 9), (0, 0), (1234, 1)):
            self.assertEqual(rules.reduce_number(number), reduced)
        for invalid in (-1, 1.5, True):
            with self.assertRaises(ValueError):
                rules.reduce_number(invalid)

    def test_panchangam_angle_formulas_and_karana_boundaries(self):
        for elongation, tithi, karana in ((0, 1, "Kimstughna"), (6, 1, "Bava"),
                                           (12, 2, "Balava"), (168, 15, "Vishti"),
                                           (342, 29, "Shakuni"), (348, 30, "Chatushpada"),
                                           (354, 30, "Naga")):
            planets = {"Sun": {"longitude": 0}, "Moon": {"longitude": elongation}}
            with patch.object(astrology, "positions", return_value=planets):
                result = astrology.panchangam(date(2000, 1, 1))
            self.assertEqual(result["tithi"]["index"], tithi)
            self.assertEqual(result["karana"], karana)
            self.assertEqual(result["yoga"]["index"], int(elongation * 27 / 360) + 1)
            self.assertEqual(result["vara"], "Saturday")

    @unittest.skipUnless(HAS_PYDANTIC, "Pydantic is not installed")
    def test_forecast_uses_ist_today_and_seven_real_dates(self):
        fixed = datetime(2026, 10, 17, 0, 15, tzinfo=ZoneInfo("Asia/Kolkata"))
        with patch("app.features.ai_reports.modules.forecast.datetime") as clock:
            clock.now.return_value = fixed
            with patch("app.features.ai_reports.modules.forecast.panchangam") as snapshot:
                snapshot.side_effect = lambda day: {"date": day.isoformat(), "transits": {"Moon": {"rasi": 0}}}
                weekly = SERVICES["forecast"].calculate(ForecastInput(rasi=11, period="weekly"))
                self.assertEqual([entry["date"] for entry in weekly["days"]],
                                 [(fixed.date() + timedelta(days=offset)).isoformat() for offset in range(7)])
                self.assertEqual(snapshot.call_count, 7)
                self.assertTrue(all(entry["houses_from_selected_rasi"]["Moon"] == 2 for entry in weekly["days"]))
                daily = SERVICES["forecast"].calculate(ForecastInput(rasi=0))
                self.assertEqual(len(daily["days"]), 1)
                clock.now.assert_called_with(ZoneInfo("Asia/Kolkata"))
                json.dumps(weekly)


@unittest.skipUnless(HAS_SWISS and HAS_PYDANTIC, "Swiss integration requires optional pyswisseph and Pydantic")
class SwissEphemerisTests(unittest.TestCase):
    def test_j2000_known_sidereal_positions(self):
        result = astrology.positions(datetime(2000, 1, 1, 12, tzinfo=timezone.utc))
        self.assertAlmostEqual(result["Sun"]["longitude"], 256.5157, delta=0.03)
        self.assertAlmostEqual(result["Moon"]["longitude"], 199.4705, delta=0.03)
        self.assertAlmostEqual((result["Ketu"]["longitude"] - result["Rahu"]["longitude"]) % 360, 180)
        moon = astrology.lunar_position(result["Moon"]["longitude"])
        self.assertEqual((moon["rasi"], moon["nakshatra"], moon["pada"]), (6, 14, 4))

    def test_explicit_flags_lahiri_and_sidereal_houses(self):
        swe = astrology.swiss()
        with patch.object(swe, "calc_ut", wraps=swe.calc_ut) as calc, \
             patch.object(swe, "set_sid_mode", wraps=swe.set_sid_mode) as sidereal, \
             patch.object(swe, "houses_ex", wraps=swe.houses_ex) as houses:
            chart = astrology.birth_chart(BirthInput(**BIRTH))
        for call in calc.call_args_list:
            self.assertTrue(call.args[2] & swe.FLG_MOSEPH)
            self.assertTrue(call.args[2] & swe.FLG_SIDEREAL)
            self.assertFalse(call.args[2] & swe.FLG_SWIEPH)
        sidereal.assert_called_with(swe.SIDM_LAHIRI)
        self.assertEqual(houses.call_args.args[-1], swe.FLG_SIDEREAL)
        self.assertEqual(chart["dosha"]["status"], "not_calculated")
        self.assertEqual(len(chart["ascendant"]["cusps"]), 12)
        self.assertTrue(0 <= chart["ascendant"]["longitude"] < 360)
        json.dumps(chart)

    def test_every_service_calculates_json_serializable_raw_data(self):
        examples = {"horoscope": BIRTH, "numerology": {"full_name": "Arul Mani", "birth_date": "2000-01-01"},
                    "compatibility": {"bride": BIRTH, "groom": BIRTH},
                    "vastu": {"facing": "W", "main_door": "E", "kitchen": "SE", "bedroom": "SW"},
                    "gemstone": BIRTH, "baby-names": BIRTH, "forecast": {"rasi": 0, "period": "weekly"}}
        for key, example in examples.items():
            with self.subTest(key=key):
                service = SERVICES[key]
                raw = service.calculate(service.input_schema.model_validate(example))
                json.dumps(raw, allow_nan=False)
                self.assertIn("calculation_version", raw["metadata"])
                self.assertIn("ephemeris", raw["metadata"])
                self.assertTrue(raw["metadata"]["limitations"])
                if key == "gemstone":
                    self.assertEqual(raw["individualized_suitability"]["status"], "not_assessed")
                    self.assertTrue(all(item["status"] == "traditional_association_only" for item in raw["associations"]))
                if key == "forecast":
                    for day in raw["days"]:
                        self.assertTrue({"tithi", "nakshatra", "vara", "yoga", "karana", "transits"} <= day.keys())


if __name__ == "__main__":
    unittest.main()