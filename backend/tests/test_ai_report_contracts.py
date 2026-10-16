"""Boundary checks runnable without a database or AI credentials."""
import unittest

from pydantic import ValidationError

from app.features.ai_reports.contracts import BirthInput, ReportRequest


class ContractTests(unittest.TestCase):
    def test_birth_coordinates_and_timezone_are_required_and_validated(self):
        inputs = dict(birth_date="2000-01-01", birth_time="12:00", place="Chennai", latitude=13.08, longitude=80.27)
        self.assertEqual(BirthInput(**inputs).timezone, "Asia/Kolkata")
        for invalid in ({"latitude": 100}, {"timezone": "invalid/place"}, {"birth_date": "1899-01-01"}):
            with self.assertRaises(ValidationError):
                BirthInput(**(inputs | invalid))

    def test_only_basic_tier_and_explicit_consent_are_accepted(self):
        self.assertEqual(ReportRequest(inputs={}, consent=True).tier, "basic")
        for invalid in ({"tier": "premium"}, {"consent": False}):
            with self.assertRaises(ValidationError):
                ReportRequest(**({"inputs": {}, "consent": True} | invalid))


if __name__ == "__main__":
    unittest.main()