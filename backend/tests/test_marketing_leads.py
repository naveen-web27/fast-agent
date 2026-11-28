"""RightConnect Marketing leads: automatic stage changes, payment state and due follow-ups."""
from datetime import date
import unittest

from app.features.marketing.rules import STATUSES, is_due, payment_state, status_after_activity, status_change_text


class StatusAfterActivityTests(unittest.TestCase):
    def test_first_contact_moves_new_lead_to_called(self):
        for kind in ("call", "whatsapp", "meeting"):
            with self.subTest(kind=kind):
                self.assertEqual(status_after_activity("new", kind), "called")

    def test_notes_and_later_contact_keep_the_stage(self):
        self.assertIsNone(status_after_activity("new", "note"))
        for status in ("called", "interested", "converted", "in_progress", "completed"):
            with self.subTest(status=status):
                self.assertIsNone(status_after_activity(status, "call"))

    def test_payment_confirms_the_deal_but_never_moves_work_backwards(self):
        for status in ("new", "called", "interested", "lost"):
            with self.subTest(status=status):
                self.assertEqual(status_after_activity(status, "payment"), "converted")
        for status in ("converted", "in_progress", "completed"):
            with self.subTest(status=status):
                self.assertIsNone(status_after_activity(status, "payment"))

    def test_every_status_has_a_readable_change_text(self):
        self.assertEqual(status_change_text("converted", "in_progress"), "Converted → Work in progress")
        for status in STATUSES:
            self.assertNotIn("_", status_change_text("new", status))


class PaymentStateTests(unittest.TestCase):
    def test_with_agreed_price(self):
        self.assertEqual(payment_state(5000, 0), "due")
        self.assertEqual(payment_state(5000, 2000), "partial")
        self.assertEqual(payment_state(5000, 5000), "paid")
        self.assertEqual(payment_state(5000, 6000), "paid")

    def test_without_price(self):
        self.assertEqual(payment_state(None, 0), "none")
        self.assertEqual(payment_state(0, 0), "none")
        self.assertEqual(payment_state(None, 1500), "paid")


class DueTests(unittest.TestCase):
    TODAY = date(2026, 11, 28)

    def test_due_today_or_late_while_open(self):
        self.assertTrue(is_due("called", date(2026, 11, 28), self.TODAY))
        self.assertTrue(is_due("interested", date(2026, 11, 20), self.TODAY))
        self.assertFalse(is_due("called", date(2026, 11, 29), self.TODAY))
        self.assertFalse(is_due("new", None, self.TODAY))

    def test_closed_leads_are_never_due(self):
        self.assertFalse(is_due("completed", date(2026, 11, 1), self.TODAY))
        self.assertFalse(is_due("lost", date(2026, 11, 1), self.TODAY))


if __name__ == "__main__":
    unittest.main()
