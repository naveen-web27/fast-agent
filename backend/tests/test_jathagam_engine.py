"""Server Jathagam engine checks (Python port of the former browser engine, Astronomy Engine 2.1.19)."""
import importlib.util
import unittest

ASTRONOMY = importlib.util.find_spec("astronomy") is not None

if ASTRONOMY:
    import astronomy as A

    from app.features.porutham import engine as J


def angle_gap(first, second):
    return abs((first - second + 180) % 360 - 180)


def synthetic(lagna, signs):
    planets = {planet: {"sign": signs[planet], "longitude": signs[planet] * 30 + 1} for planet in J.PLANET_ORDER}
    return {"utc_ms": 0, "lagna": {"sign": lagna}, "planets": planets}


BASE = {"Sun": 1, "Moon": 0, "Mars": 6, "Mercury": 1, "Jupiter": 9, "Venus": 2, "Saturn": 10, "Rahu": 3, "Ketu": 9}


def ms(time):
    return time.ut * J.DAY_MS + J.J2000_MS


@unittest.skipUnless(ASTRONOMY, "astronomy-engine is not installed")
class JathagamEngineTests(unittest.TestCase):
    def test_j2000_matches_swiss_ephemeris_lahiri_reference(self):
        chart = J.chart_at(946_728_000_000, 13.0827, 80.2707)
        self.assertAlmostEqual(chart["planets"]["Sun"]["longitude"], 256.5157, delta=0.01)
        self.assertAlmostEqual(chart["planets"]["Moon"]["longitude"], 199.4705, delta=0.01)
        self.assertEqual((chart["planets"]["Moon"]["star"], chart["planets"]["Moon"]["pada"]), (14, 4))
        self.assertAlmostEqual(chart["ayanamsa"], 23.853, delta=0.002)
        self.assertAlmostEqual(angle_gap(chart["planets"]["Rahu"]["longitude"], chart["planets"]["Ketu"]["longitude"]), 180, delta=1e-9)
        self.assertTrue(chart["planets"]["Rahu"]["retrograde"])
        self.assertEqual(chart["planets"]["Rahu"]["sign"], 3)

    def test_local_time_conversion_and_dst_rejection(self):
        self.assertEqual(J.local_to_utc("2000-01-01", "17:30", "Asia/Kolkata"), 946728000000)
        self.assertEqual(J.local_to_utc("2024-07-01", "09:15:30", "Europe/London"), 1719821730000)
        with self.assertRaisesRegex(ValueError, "nonexistent-time"):
            J.local_to_utc("2024-03-10", "02:30", "America/New_York")
        with self.assertRaisesRegex(ValueError, "ambiguous-time"):
            J.local_to_utc("2024-11-03", "01:30", "America/New_York")

    def test_lagna_equals_sun_at_sunrise_and_opposes_it_at_sunset(self):
        chennai = A.Observer(13.0827, 80.2707, 0)
        rise = A.SearchRiseSet(A.Body.Sun, chennai, A.Direction.Rise, A.Time.Make(2024, 4, 13, 18, 0, 0), 2)
        sunset = A.SearchRiseSet(A.Body.Sun, chennai, A.Direction.Set, A.Time.Make(2024, 4, 14, 6, 0, 0), 2)
        at_rise = J.chart_at(ms(rise), 13.0827, 80.2707)
        at_set = J.chart_at(ms(sunset), 13.0827, 80.2707)
        self.assertLess(angle_gap(at_rise["lagna"]["longitude"], at_rise["planets"]["Sun"]["longitude"]), 1.5)
        self.assertLess(angle_gap(at_set["lagna"]["longitude"], at_set["planets"]["Sun"]["longitude"] + 180), 1.5)

    def test_vimshottari_and_bhukti_arithmetic(self):
        periods = J.vimshottari(0, 0)
        sub = J.bhuktis(periods[1])
        self.assertEqual((periods[0]["lord"], periods[1]["lord"], sub[0]["lord"]), ("Ketu", "Venus", "Venus"))
        self.assertAlmostEqual((periods[0]["end"] - periods[0]["start"]) / J.YEAR_MS, 7)
        self.assertAlmostEqual(sub[8]["end"] - sub[0]["start"], periods[1]["end"] - periods[1]["start"], delta=1)

    def test_navamsa_and_dignity_tables(self):
        self.assertEqual([J.placement(lon, False)["navamsa"] for lon in (0, 3.34, 30, 359.99)], [0, 1, 9, 11])
        self.assertEqual([J.dignity("Sun", 0), J.dignity("Sun", 6), J.dignity("Mars", 7), J.dignity("Jupiter", 2)],
                         ["exalted", "debilitated", "own", ""])

    def test_chevvai_rahu_ketu_papa_and_seventh_house(self):
        mars_seventh = J.analyse_person(synthetic(0, BASE), 0)
        mars_own = J.analyse_person(synthetic(5, dict(BASE, Mars=0, Moon=5)), 0)
        mars_clear = J.analyse_person(synthetic(0, dict(BASE, Mars=2, Moon=0)), 0)
        self.assertEqual(mars_seventh["chevvai"], {"from_lagna": 7, "from_moon": 7, "raw": True, "cancellations": [], "dosha": True})
        self.assertEqual(mars_own["chevvai"]["from_lagna"], 8)
        self.assertEqual(mars_own["chevvai"]["cancellations"], ["ownSign"])
        self.assertFalse(mars_own["chevvai"]["dosha"])
        self.assertFalse(mars_clear["chevvai"]["raw"])
        self.assertEqual(mars_seventh["rahu_ketu"], {"rahu_house": 4, "ketu_house": 10, "dosha": False})
        # From Lagna and Moon (Mesham): Sun 2nd, Mars 7th, Rahu 4th; from Venus (Mithunam): Sun 12th, Rahu 2nd, Ketu 8th.
        self.assertEqual(mars_seventh["papa"]["total"], 9)
        seventh = mars_seventh["seventh"]
        self.assertEqual((seventh["sign"], seventh["lord"], seventh["lord_house"], seventh["occupants"]), (6, "Venus", 3, ["Mars"]))

    def test_dasa_quality_follows_functional_nature_for_mesha_lagna(self):
        quality = {planet: J.dasa_quality(synthetic(0, BASE), planet)["level"] for planet in ("Sun", "Mars", "Mercury", "Jupiter", "Saturn", "Rahu")}
        self.assertEqual(quality, {"Sun": "good", "Mars": "good", "Mercury": "challenging", "Jupiter": "good", "Saturn": "mixed", "Rahu": "mixed"})

    def test_life_areas_use_house_lords_and_occupants(self):
        life = J.analyse_person(synthetic(0, BASE), 0)["life"]
        self.assertEqual([life["career"]["lord"], life["career"]["level"], life["career"]["period"]["maha"], life["career"]["period"]["bhukti"]],
                         ["Saturn", "strong", "Ketu", "Saturn"])
        self.assertEqual(life["health"]["level"], "moderate")
        self.assertEqual([life["children"]["level"], life["children"]["jupiter_house"]], ["care", 10])
        self.assertEqual(life["marriage"]["level"], "care")

    def test_next_period_search_uses_bhukti_granularity(self):
        periods = J.vimshottari(0, 0)
        soon = J.next_period_of(periods, ["Venus"], 0, 20 * J.YEAR_MS)
        self.assertEqual((soon["maha"], soon["bhukti"]), ("Ketu", "Venus"))
        self.assertIsNone(J.next_period_of(periods, ["Mercury"], 0, J.YEAR_MS))
        whole = J.next_period_of(periods, ["Ketu"], 0, J.YEAR_MS)
        self.assertEqual((whole["maha"], whole["bhukti"], whole["start"]), ("Ketu", None, 0))
        self.assertAlmostEqual(whole["end"], 7 * 365.2425 * 86400000, delta=1)

    def test_joint_timeline_is_contiguous_and_splits_at_each_mahadasa_change(self):
        groom = synthetic(0, dict(BASE, Moon=3))
        groom["planets"]["Moon"]["longitude"] = 91
        timeline = J.analyse_pair(synthetic(0, BASE), groom, 0)["timeline"]
        self.assertEqual(timeline[0]["start"], 0)
        self.assertAlmostEqual(timeline[-1]["end"], 25 * J.YEAR_MS, delta=1)
        self.assertTrue(all(index == 0 or row["start"] == timeline[index - 1]["end"] for index, row in enumerate(timeline)))
        self.assertTrue(all(p["start"] <= row["start"] < p["end"] for row in timeline for p in (row["bride"], row["groom"])))
        # Bride: Ketu then Venus. Groom at 91 degrees: Jupiter, Saturn, Mercury.
        self.assertEqual([[row["groom"]["lord"], row["bride"]["lord"]] for row in timeline],
                         [["Jupiter", "Ketu"], ["Saturn", "Ketu"], ["Saturn", "Venus"], ["Mercury", "Venus"]])


if __name__ == "__main__":
    unittest.main()
