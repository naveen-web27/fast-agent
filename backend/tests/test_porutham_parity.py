"""Browser Porutham rules must agree with the Python rules for every star and Rasi pair."""
import json
import shutil
import subprocess
import unittest
from pathlib import Path

from app.features.ai_reports import rules

SCRIPT = Path(__file__).parents[2] / "frontend/assets/porutham-rules.js"
KEYS = ["dina", "gana", "mahendra", "stree_deergha", "yoni", "rasi",
        "rasi_adhipathi", "vasiya", "rajju", "vedha", "nadi", "varna"]
CASES = [(bride, groom, 0, 0) for bride in range(27) for groom in range(27)]
CASES += [(0, 13, bride, groom) for bride in range(12) for groom in range(12)]

JXA = """
ObjC.import('Foundation');
var source = $.NSString.stringWithContentsOfFileEncodingError(%s, $.NSUTF8StringEncoding, null).js;
(0, eval)(source);
var cases = %s;
JSON.stringify({
  results: cases.map(function (c) {
    var r = PoruthamRules.calculate(c[0], c[1], c[2], c[3]);
    return r.checks.map(function (check) { return check.matches; });
  }),
  stars: [0,1,2,3,4,5,6,7,8,9,10,11].map(function (rasi) {
    return PoruthamRules.starsForRasi(rasi).map(function (s) { return [s.star, s.padas]; });
  })
});
"""


@unittest.skipUnless(shutil.which("osascript"), "JavaScriptCore via osascript is only available on macOS")
class PoruthamParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        script = JXA % (json.dumps(str(SCRIPT)), json.dumps(CASES))
        output = subprocess.run(["osascript", "-l", "JavaScript", "-e", script],
                                check=True, capture_output=True, text=True).stdout
        cls.browser = json.loads(output)

    def test_every_pair_matches_python(self):
        for case, browser in zip(CASES, self.browser["results"], strict=True):
            python = {check["key"]: check["matches_rule"] for check in rules.porutham(*case)["checks"]}
            self.assertEqual(browser, [python[key] for key in KEYS], case)

    def test_rasi_filters_its_nine_padas(self):
        stars = self.browser["stars"]
        self.assertEqual(stars[0], [[0, [1, 2, 3, 4]], [1, [1, 2, 3, 4]], [2, [1]]])
        self.assertEqual(stars[2], [[4, [3, 4]], [5, [1, 2, 3, 4]], [6, [1, 2, 3]]])
        for rasi_stars in stars:
            self.assertEqual(sum(len(padas) for _, padas in rasi_stars), 9)


if __name__ == "__main__":
    unittest.main()
