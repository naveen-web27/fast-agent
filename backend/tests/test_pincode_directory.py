"""Place search input handling and the bundled India Post PIN directory (no database needed)."""
import ast
import csv
import gzip
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).parents[1]
SERVICE = ROOT / "app/features/locations/service.py"
DATA = ROOT.parent / "db/data/pincode_areas.csv.gz"


def load():
    tree = ast.parse(SERVICE.read_text(), filename=str(SERVICE))
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"clean_query", "_prefix"}]
    namespace = {"re": re}
    exec(compile(ast.fix_missing_locations(ast.Module(body=body, type_ignores=[])), str(SERVICE), "exec"), namespace)
    return SimpleNamespace(**namespace)


service = load()


class QueryTests(unittest.TestCase):
    def test_digits_search_pin_codes(self):
        self.assertEqual(service.clean_query("637 101"), ("pincode", "637101"))
        self.assertEqual(service.clean_query("6371019"), ("pincode", "637101"))
        self.assertIsNone(service.clean_query("63"))

    def test_words_are_normalised(self):
        self.assertEqual(service.clean_query("  Edappadi  "), ("name", "edappadi"))
        self.assertEqual(service.clean_query("T. Nagar"), ("name", "t. nagar"))
        self.assertEqual(service.clean_query("salem<script>"), ("name", "salemscript"))
        self.assertIsNone(service.clean_query("a"))

    def test_like_wildcards_are_escaped(self):
        self.assertEqual(service._prefix("50%_off"), "50\\%\\_off%")


class DirectoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with gzip.open(DATA, "rt", encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))

    def test_covers_all_of_india(self):
        self.assertGreater(len(self.rows), 150_000)
        self.assertGreater(len({row["pincode"] for row in self.rows}), 19_000)
        self.assertTrue(all(re.fullmatch(r"[1-9][0-9]{5}", row["pincode"]) for row in self.rows))

    def test_examples_resolve(self):
        idappadi = [row for row in self.rows if row["area"] == "Idappadi"]
        self.assertEqual({(row["pincode"], row["district"], row["state"]) for row in idappadi}, {("637101", "Salem", "Tamil Nadu")})
        self.assertGreater(sum(1 for row in self.rows if row["district"] == "Salem"), 100)
        self.assertTrue(any(row["pincode"] == "600042" and row["area"] == "Velacheri" for row in self.rows))

    def test_states_are_current(self):
        states = {row["pincode"][:2]: row["state"] for row in self.rows if row["pincode"].startswith(("500", "194"))}
        self.assertEqual(states.get("50"), "Telangana")
        self.assertIn("Ladakh", {row["state"] for row in self.rows if row["district"] == "Leh"})
        self.assertNotIn("Pondicherry", {row["state"] for row in self.rows})


if __name__ == "__main__":
    unittest.main()
