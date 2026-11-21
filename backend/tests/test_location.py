"""PIN code validation and "nearest first" scoring (app/core/location.py), loaded without SQLAlchemy."""
import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

PATH = Path(__file__).parents[1] / "app/core/location.py"
NAMES = {"PINCODE_PATTERN", "SAME_AREA", "SAME_DISTRICT", "SAME_STATE", "SAME_REGION", "ELSEWHERE", "STATE_BY_PREFIX",
         "_circles", "normalize_pincode", "same_state_prefixes", "proximity"}


def load():
    tree = ast.parse(PATH.read_text(), filename=str(PATH))
    body = [
        node for node in tree.body
        if (isinstance(node, ast.FunctionDef) and node.name in NAMES)
        or (isinstance(node, ast.Assign) and any(getattr(t, "id", None) in NAMES for t in getattr(node.targets[0], "elts", node.targets)))
    ]
    namespace = {"re": re}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), str(PATH), "exec"), namespace)
    return SimpleNamespace(**namespace)


location = load()


class PincodeTests(unittest.TestCase):
    def test_valid_codes_are_compacted(self):
        self.assertEqual(location.normalize_pincode("600 042"), "600042")
        self.assertEqual(location.normalize_pincode(" 110001 "), "110001")
        self.assertIsNone(location.normalize_pincode(""))
        self.assertIsNone(location.normalize_pincode(None))

    def test_invalid_codes_are_rejected(self):
        for value in ["060042", "60004", "6000421", "60004a", "600-042"]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "6-digit PIN"):
                location.normalize_pincode(value)

    def test_nearness_follows_the_pin_hierarchy(self):
        near = "600042"  # Velachery, Chennai
        self.assertEqual(location.proximity("600042", None, near, None), location.SAME_AREA)
        self.assertEqual(location.proximity("600017", None, near, None), location.SAME_DISTRICT)  # T. Nagar
        self.assertEqual(location.proximity("641001", None, near, None), location.SAME_STATE)  # Coimbatore
        self.assertEqual(location.proximity("605001", None, near, None), location.SAME_STATE)  # Puducherry, same circle
        self.assertEqual(location.proximity("560001", None, near, None), location.ELSEWHERE)  # Bengaluru: region 5
        self.assertEqual(location.proximity("682001", None, near, None), location.SAME_REGION)  # Kochi: region 6, other state
        self.assertEqual(location.proximity("110001", None, near, None), location.ELSEWHERE)  # Delhi
        self.assertEqual(location.proximity(None, None, near, None), location.ELSEWHERE)

    def test_city_helps_profiles_without_a_pin(self):
        self.assertEqual(location.proximity(None, " Chennai ", "600042", "chennai"), location.SAME_DISTRICT)
        self.assertEqual(location.proximity("600042", "Chennai", "600042", "Chennai"), location.SAME_AREA)
        self.assertEqual(location.proximity(None, None, None, None), location.ELSEWHERE)


if __name__ == "__main__":
    unittest.main()
