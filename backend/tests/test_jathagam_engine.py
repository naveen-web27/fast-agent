"""Browser Jathagam engine checks, executed in JavaScriptCore with the vendored Astronomy Engine."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

ASSETS = Path(__file__).parents[2] / "frontend/assets"
SCRIPTS = [ASSETS / "vendor/astronomy-engine-2.1.19.min.js", ASSETS / "jathagam.js"]

JXA = """
ObjC.import('Foundation');
%s.forEach(function (path) {
  (0, eval)($.NSString.stringWithContentsOfFileEncodingError(path, $.NSUTF8StringEncoding, null).js);
});
var J = JathagamEngine, A = Astronomy;
function attempt(fn) { try { return fn(); } catch (e) { return 'error:' + e.message; } }
function sidereal(utcMs) { var c = J.chartAt(utcMs, 13.0827, 80.2707); return c; }
var j2000 = sidereal(Date.UTC(2000, 0, 1, 12));
var chennai = new A.Observer(13.0827, 80.2707, 0);
var rise = A.SearchRiseSet(A.Body.Sun, chennai, +1, A.MakeTime(new Date(Date.UTC(2024, 3, 13, 18))), 2);
var set = A.SearchRiseSet(A.Body.Sun, chennai, -1, A.MakeTime(new Date(Date.UTC(2024, 3, 14, 6))), 2);
var atRise = J.chartAt(rise.date.getTime(), 13.0827, 80.2707);
var atSet = J.chartAt(set.date.getTime(), 13.0827, 80.2707);
var periods = J.vimshottari(0, 0);
var sub = J.bhuktis(periods[1]);
function synthetic(lagna, signs) {
  var planets = {};
  ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'].forEach(function (p) {
    planets[p] = { sign: signs[p], longitude: signs[p] * 30 + 1 };
  });
  return { utcMs: 0, lagna: { sign: lagna }, planets: planets };
}
var base = { Sun: 1, Moon: 0, Mars: 6, Mercury: 1, Jupiter: 9, Venus: 2, Saturn: 10, Rahu: 3, Ketu: 9 };
var marsSeventh = J.analysePerson(synthetic(0, base), 0);
var marsOwn = J.analysePerson(synthetic(5, Object.assign({}, base, { Mars: 0, Moon: 5 })), 0);
var marsClear = J.analysePerson(synthetic(0, Object.assign({}, base, { Mars: 2, Moon: 0 })), 0);
var quality = {};
['Sun', 'Mars', 'Mercury', 'Jupiter', 'Saturn', 'Rahu'].forEach(function (p) { quality[p] = J.dasaQuality(synthetic(0, base), p).level; });
var life = marsSeventh.life;
var groomChart = synthetic(0, Object.assign({}, base, { Moon: 3 }));
groomChart.planets.Moon.longitude = 91;
var timeline = J.analysePair(synthetic(0, base), groomChart, 0).timeline;
var horizonEnd = 25 * J.YEAR_MS;
var venusSoon = J.nextPeriodOf(periods, ['Venus'], 0, 20 * J.YEAR_MS);
JSON.stringify({
  j2000: { sun: j2000.planets.Sun.longitude, moon: j2000.planets.Moon.longitude, moonStar: j2000.planets.Moon.star,
           moonPada: j2000.planets.Moon.pada, rahu: j2000.planets.Rahu.longitude, ketu: j2000.planets.Ketu.longitude,
           rahuRetro: j2000.planets.Rahu.retrograde, lagna: j2000.lagna.longitude, ayanamsa: j2000.ayanamsa },
  ist: J.localToUtc('2000-01-01', '17:30', 'Asia/Kolkata'),
  london: J.localToUtc('2024-07-01', '09:15:30', 'Europe/London'),
  gap: attempt(function () { return J.localToUtc('2024-03-10', '02:30', 'America/New_York'); }),
  fold: attempt(function () { return J.localToUtc('2024-11-03', '01:30', 'America/New_York'); }),
  sunrise: { lagna: atRise.lagna.longitude, sun: atRise.planets.Sun.longitude },
  sunset: { lagna: atSet.lagna.longitude, sun: atSet.planets.Sun.longitude },
  dasa: { first: periods[0].lord, firstYears: (periods[0].end - periods[0].start) / J.YEAR_MS, second: periods[1].lord,
          bhuktiFirst: sub[0].lord, bhuktiSpan: sub[8].end - sub[0].start, mahaSpan: periods[1].end - periods[1].start },
  navamsa: [0, 3.34, 30, 359.99].map(function (lon) { return Math.floor(lon * 3 / 10) %% 12; }),
  dignity: [J.dignity('Sun', 0), J.dignity('Sun', 6), J.dignity('Mars', 7), J.dignity('Jupiter', 2)],
  marsSeventh: marsSeventh.chevvai, marsOwn: marsOwn.chevvai, marsClear: marsClear.chevvai,
  rahuKetu: marsSeventh.rahuKetu, papa: marsSeventh.papa.total, seventh: marsSeventh.seventh,
  quality: quality,
  periodQuality: marsSeventh.dasa.periods.every(function (p) { return ['good', 'mixed', 'challenging'].indexOf(p.quality) >= 0; }),
  life: { career: [life.career.lord, life.career.level, life.career.period.maha, life.career.period.bhukti],
          health: life.health.level, children: [life.children.level, life.children.jupiterHouse], marriage: life.marriage.level },
  venusSoon: [venusSoon.maha, venusSoon.bhukti],
  mercuryWithinYear: J.nextPeriodOf(periods, ['Mercury'], 0, J.YEAR_MS),
  ketuWhole: J.nextPeriodOf(periods, ['Ketu'], 0, J.YEAR_MS),
  timeline: { rows: timeline.length, first: timeline[0].start, last: timeline[timeline.length - 1].end - horizonEnd,
              contiguous: timeline.every(function (r, i) { return i === 0 || r.start === timeline[i - 1].end; }),
              covered: timeline.every(function (r) { return [r.bride, r.groom].every(function (p) { return p.start <= r.start && r.start < p.end; }); }),
              lords: timeline.map(function (r) { return [r.groom.lord, r.bride.lord]; }) }
});
"""


def angle_gap(first, second):
    return abs((first - second + 180) % 360 - 180)


@unittest.skipUnless(shutil.which("osascript"), "JavaScriptCore via osascript is only available on macOS")
class JathagamEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = JXA % json.dumps([str(path) for path in SCRIPTS])
        output = subprocess.run(["osascript", "-l", "JavaScript", "-e", script],
                                check=True, capture_output=True, text=True).stdout
        cls.r = json.loads(output)

    def test_j2000_matches_swiss_ephemeris_lahiri_reference(self):
        # Same Swiss Ephemeris reference values as test_ai_report_calculations.SwissEphemerisTests.
        j2000 = self.r["j2000"]
        self.assertAlmostEqual(j2000["sun"], 256.5157, delta=0.01)
        self.assertAlmostEqual(j2000["moon"], 199.4705, delta=0.01)
        self.assertEqual((j2000["moonStar"], j2000["moonPada"]), (14, 4))
        self.assertAlmostEqual(j2000["ayanamsa"], 23.853, delta=0.002)
        self.assertAlmostEqual(angle_gap(j2000["rahu"], j2000["ketu"]), 180, delta=1e-9)
        self.assertTrue(j2000["rahuRetro"])
        self.assertEqual(int(j2000["rahu"] // 30), 3)

    def test_local_time_conversion_and_dst_rejection(self):
        self.assertEqual(self.r["ist"], 946728000000)
        self.assertEqual(self.r["london"], 1719821730000)
        self.assertEqual(self.r["gap"], "error:nonexistent-time")
        self.assertEqual(self.r["fold"], "error:ambiguous-time")

    def test_lagna_equals_sun_at_sunrise_and_opposes_it_at_sunset(self):
        self.assertLess(angle_gap(self.r["sunrise"]["lagna"], self.r["sunrise"]["sun"]), 1.5)
        self.assertLess(angle_gap(self.r["sunset"]["lagna"], self.r["sunset"]["sun"] + 180), 1.5)

    def test_vimshottari_and_bhukti_arithmetic(self):
        dasa = self.r["dasa"]
        self.assertEqual((dasa["first"], dasa["second"], dasa["bhuktiFirst"]), ("Ketu", "Venus", "Venus"))
        self.assertAlmostEqual(dasa["firstYears"], 7)
        self.assertAlmostEqual(dasa["bhuktiSpan"], dasa["mahaSpan"], delta=1)

    def test_navamsa_and_dignity_tables(self):
        self.assertEqual(self.r["navamsa"], [0, 1, 9, 11])
        self.assertEqual(self.r["dignity"], ["exalted", "debilitated", "own", ""])

    def test_chevvai_rahu_ketu_papa_and_seventh_house(self):
        self.assertEqual(self.r["marsSeventh"], {"fromLagna": 7, "fromMoon": 7, "raw": True, "cancellations": [], "dosha": True})
        self.assertEqual(self.r["marsOwn"]["fromLagna"], 8)
        self.assertEqual(self.r["marsOwn"]["cancellations"], ["ownSign"])
        self.assertFalse(self.r["marsOwn"]["dosha"])
        self.assertFalse(self.r["marsClear"]["raw"])
        self.assertEqual(self.r["rahuKetu"], {"rahuHouse": 4, "ketuHouse": 10, "dosha": False})
        # From Lagna and Moon (Mesham): Sun 2nd, Mars 7th, Rahu 4th; from Venus (Mithunam): Sun 12th, Rahu 2nd, Ketu 8th.
        self.assertEqual(self.r["papa"], 9)
        self.assertEqual(self.r["seventh"]["sign"], 6)
        self.assertEqual(self.r["seventh"]["lord"], "Venus")
        self.assertEqual(self.r["seventh"]["lordHouse"], 3)
        self.assertEqual(self.r["seventh"]["occupants"], ["Mars"])

    def test_dasa_quality_follows_functional_nature_for_mesha_lagna(self):
        # Sun rules the 5th; Mars rules the Lagna and sits in a kendra; Mercury rules only the 3rd and 6th;
        # debilitated Jupiter still rules the 9th and sits in the 10th; Rahu in the 4th is neutral.
        self.assertEqual(self.r["quality"], {"Sun": "good", "Mars": "good", "Mercury": "challenging",
                                             "Jupiter": "good", "Saturn": "mixed", "Rahu": "mixed"})
        self.assertTrue(self.r["periodQuality"])

    def test_life_areas_use_house_lords_and_occupants(self):
        life = self.r["life"]
        # 10th lord Saturn is in its own sign and Jupiter occupies the 10th.
        self.assertEqual(life["career"], ["Saturn", "strong", "Ketu", "Saturn"])
        self.assertEqual(life["health"], "moderate")
        # 5th lord Sun gains nothing and Jupiter is debilitated.
        self.assertEqual(life["children"], ["care", 10])
        # Mars occupies the 7th.
        self.assertEqual(life["marriage"], "care")

    def test_next_period_search_uses_bhukti_granularity(self):
        self.assertEqual(self.r["venusSoon"], ["Ketu", "Venus"])
        self.assertIsNone(self.r["mercuryWithinYear"])
        whole = self.r["ketuWhole"]
        self.assertEqual((whole["maha"], whole["bhukti"], whole["start"]), ("Ketu", None, 0))
        self.assertAlmostEqual(whole["end"], 7 * 365.2425 * 86400000, delta=1)

    def test_joint_timeline_is_contiguous_and_splits_at_each_mahadasa_change(self):
        timeline = self.r["timeline"]
        self.assertEqual(timeline["first"], 0)
        self.assertAlmostEqual(timeline["last"], 0, delta=1)
        self.assertTrue(timeline["contiguous"])
        self.assertTrue(timeline["covered"])
        # Bride: Ketu then Venus (about 6.5 years). Groom at 91 degrees: Jupiter, Saturn (2.8 years), Mercury (21.8 years).
        self.assertEqual(timeline["lords"], [["Jupiter", "Ketu"], ["Saturn", "Ketu"], ["Saturn", "Venus"], ["Mercury", "Venus"]])


if __name__ == "__main__":
    unittest.main()
