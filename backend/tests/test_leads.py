"""Leads: phone cleaning, reading pasted spreadsheet values, and merging imports without overwriting entered data."""
import ast
from datetime import date
from pathlib import Path
from types import SimpleNamespace
import unittest

from app.features.leads.parsing import clean_phone, clip, guess_status, guess_type, parse_date

ROOT = Path(__file__).parents[1]


def load_service_helpers():
    """clean_import_row, merge_into and _Draft from service.py, without SQLAlchemy (not installed for these tests)."""
    path = ROOT / "app/features/leads/service.py"
    tree = ast.parse(path.read_text(), filename=str(path))
    wanted = {"clean_import_row", "merge_into", "_Draft", "TEXT_LIMITS"}
    body = [
        node for node in tree.body
        if (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in wanted)
        or (isinstance(node, ast.Assign) and any(getattr(target, "id", None) in wanted for target in node.targets))
    ]
    namespace = {"clean_phone": clean_phone, "clip": clip, "guess_status": guess_status, "guess_type": guess_type, "parse_date": parse_date}
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *body], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


def row(**fields):
    defaults = dict.fromkeys(("phone", "full_name", "lead_type", "business_name", "service", "city", "status", "follow_up_on", "notes", "source"))
    return SimpleNamespace(**{**defaults, **fields})


class PhoneTests(unittest.TestCase):
    def test_indian_numbers_in_any_common_format(self):
        for value in ("9876543210", "98765 43210", "+91 98765-43210", "919876543210", "09876543210", "(+91) 98765 43210", "9876543210.0"):
            with self.subTest(value=value):
                self.assertEqual(clean_phone(value), "+919876543210")

    def test_other_countries_need_a_plus(self):
        self.assertEqual(clean_phone("+971 50 123 4567"), "+971501234567")
        self.assertEqual(clean_phone("00971501234567"), "+971501234567")

    def test_rejects_things_that_are_not_mobile_numbers(self):
        for value in ("", "12345", "1234567890", "hello", "9.87654E+09"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                clean_phone(value)


class GuessTests(unittest.TestCase):
    def test_type(self):
        self.assertEqual(guess_type("Shop owner"), "company")
        self.assertEqual(guess_type("Hotel cook"), "worker")
        self.assertEqual(guess_type("Tax Consultant"), "expert")
        self.assertEqual(guess_type("company"), "company")
        self.assertEqual(guess_type("Customer"), "customer")
        self.assertEqual(guess_type(""), "unknown")
        self.assertEqual(guess_type("??"), "unknown")

    def test_status(self):
        self.assertEqual(guess_status("Not interested"), "not_interested")
        self.assertEqual(guess_status("interested"), "interested")
        self.assertEqual(guess_status("Call back Monday"), "follow_up")
        self.assertEqual(guess_status("Follow-up"), "follow_up")
        self.assertEqual(guess_status("Called, no response"), "contacted")
        self.assertEqual(guess_status("Signed up"), "signed_up")
        self.assertEqual(guess_status("signed_up"), "signed_up")
        self.assertIsNone(guess_status(""))
        self.assertIsNone(guess_status("hmm"))

    def test_dates_are_day_first(self):
        self.assertEqual(parse_date("05/12/2026"), date(2026, 12, 5))
        self.assertEqual(parse_date("2026-12-05"), date(2026, 12, 5))
        self.assertEqual(parse_date("5-12-26"), date(2026, 12, 5))
        self.assertIsNone(parse_date("next week"))


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.svc = load_service_helpers()

    def test_clean_row(self):
        fields = self.svc.clean_import_row(row(phone="98765 43210", full_name="  Ravi   Kumar ", lead_type="shop", status="", notes="Wants listing\nCall after 6"), "WhatsApp ad")
        self.assertEqual(fields["phone"], "+919876543210")
        self.assertEqual(fields["full_name"], "Ravi Kumar")
        self.assertEqual((fields["lead_type"], fields["status"], fields["source"]), ("company", None, "WhatsApp ad"))
        self.assertEqual(fields["notes"], "Wants listing\nCall after 6")
        with self.assertRaises(ValueError):
            self.svc.clean_import_row(row(full_name="No number"), None)

    def test_merge_fills_gaps_but_never_overwrites(self):
        lead = SimpleNamespace(full_name="Ravi", business_name=None, service=None, city=None, source="Ad 1", follow_up_on=None,
                               lead_type="unknown", status="contacted", notes="First call")
        changed = self.svc.merge_into(lead, {"full_name": "Ravi K", "business_name": "Ravi Mobiles", "source": "Ad 2", "lead_type": "company",
                                             "status": "interested", "notes": "Second call", "follow_up_on": date(2026, 12, 1)})
        self.assertTrue(changed)
        self.assertEqual((lead.full_name, lead.business_name, lead.source, lead.lead_type), ("Ravi", "Ravi Mobiles", "Ad 1", "company"))
        self.assertEqual(lead.status, "contacted")
        self.assertEqual(lead.notes, "First call\nSecond call")
        self.assertFalse(self.svc.merge_into(lead, {"notes": "Second call"}))

    def test_repeated_numbers_in_one_paste_are_merged(self):
        first = {"phone": "+919876543210", "full_name": None, "lead_type": "unknown", "status": None, "notes": None}
        self.svc.merge_into(self.svc._Draft(first), {"full_name": "Ravi", "lead_type": "worker", "status": "interested"})
        self.assertEqual((first["full_name"], first["lead_type"], first["status"]), ("Ravi", "worker", "interested"))


if __name__ == "__main__":
    unittest.main()
