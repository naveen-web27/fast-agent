"""Server-side porutham report: preview redaction, payment binding and the 12-check builder."""
import asyncio
import hashlib
import hmac
import importlib.util
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

ASTRONOMY = importlib.util.find_spec("astronomy") is not None
if ASTRONOMY:
    from app.features.porutham import report, service

NOW = 1_792_756_800_000
COUPLE = {
    "language": "ta", "selected": None,
    "bride": {"name": "Priya", "birth_date": "1996-05-14", "birth_time": "06:30:00", "place": "Madurai",
              "latitude": 9.9252, "longitude": 78.1198, "timezone": "Asia/Kolkata"},
    "groom": {"name": "Karthik", "birth_date": "1993-11-02", "birth_time": "21:15:00", "place": "Chennai",
              "latitude": 13.0827, "longitude": 80.2707, "timezone": "Asia/Kolkata"},
}
SETTINGS = SimpleNamespace(razorpay_key_id="rzp_test_unit", razorpay_key_secret="unit-secret",
                           razorpay_kattam_report_amount_paise=9900, app_base_url="https://dev.example")


def strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, str):
        yield value


@unittest.skipUnless(ASTRONOMY, "astronomy-engine is not installed")
class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = service.build(COUPLE, NOW)
        cls.preview = report.preview(cls.full, "ta")
        cls.sections = {section["key"]: section for section in cls.preview["sections"]}

    def test_section_order_puts_rasi_first_and_checks_before_summary(self):
        self.assertEqual([s["key"] for s in self.full["sections"]],
                         ["rasi", "dosha", "together", "dasa", "timeline", "life", "checks", "summary", "expert"])
        self.assertTrue(self.sections["checks"]["title"].startswith("6."))
        self.assertTrue(self.sections["summary"]["title"].startswith("7."))

    def test_free_sections_are_complete(self):
        full = {s["key"]: s for s in self.full["sections"]}
        for key in ("rasi", "dosha"):
            self.assertEqual(self.sections[key]["blocks"], full[key]["blocks"])

    def test_paid_text_never_appears_in_preview(self):
        visible = set(strings(self.preview))
        full = {s["key"]: s for s in self.full["sections"]}
        self.assertFalse(set(full["summary"]["blocks"][0]["lines"]) & visible)
        dasa = {p for block in full["dasa"]["blocks"] if block["type"] == "items" for entry in block["items"] for p in entry["paragraphs"]}
        self.assertFalse(dasa & visible)
        expert = {block["text"] for block in full["expert"]["blocks"] if block["type"] in ("note", "help")}
        expert |= {value["text"] for block in full["expert"]["blocks"] if block["type"] == "table" for row in block["rows"] for value in row[1:]}
        expert |= {c["planets"] for block in full["expert"]["blocks"] if block["type"] == "charts" for chart in block["charts"] for c in chart["cells"]}
        free = {text for key in ("rasi", "dosha") for text in strings(self.sections[key])}
        self.assertFalse({text for text in expert if len(text) > 2} & visible - free)

    def test_timeline_first_two_rows_free_last_three_periods_visible(self):
        rows = self.sections["timeline"]["blocks"][1]["rows"]
        for row in rows[:2]:
            self.assertTrue(all("text" in value for value in row))
        for position, row in enumerate(rows[2:], start=2):
            self.assertTrue(all("hidden" in value for value in row[1:]))
            self.assertEqual("text" in row[0], position >= max(2, len(rows) - 3))

    def test_life_shows_headings_and_one_line(self):
        for block in self.sections["life"]["blocks"]:
            if block["type"] == "items":
                for entry in block["items"]:
                    self.assertTrue(entry["title"] and entry["badge"])
                    self.assertEqual(len(entry["paragraphs"]), 1)
                    self.assertTrue(entry["hidden"])

    def test_checks_show_two_rows_then_lock(self):
        entries = self.sections["checks"]["blocks"][0]["items"]
        self.assertTrue(all(entry.get("hidden") is None or entry["title"] for entry in entries[:2]))
        self.assertTrue(all(entry["title"] is None and entry["tone"] == "locked" for entry in entries[2:]))

    def test_english_and_rasi_report_build(self):
        english = service.build(dict(COUPLE, language="en"), NOW)
        self.assertEqual(english["parts"]["rasi"], "Rasi / Nakshatra porutham — the 12 checks")
        quick = report.rasi_report({"name": "A", "rasi": 0, "nakshatra": 0}, {"name": "B", "rasi": 4, "nakshatra": 9}, "en")
        self.assertEqual(len(quick["blocks"][-1]["items"]), 12)
        self.assertEqual(quick["matched"], sum(entry["tone"] == "good" for entry in quick["blocks"][-1]["items"]))

    def test_stars_for_rasi_covers_every_pada_once(self):
        self.assertEqual(report.stars_for_rasi(0), [0, 1, 2])
        self.assertEqual(sum(len(report.stars_for_rasi(rasi)) for rasi in range(12)), 36)

    def test_nonexistent_local_time_is_a_422(self):
        gap = dict(COUPLE, bride=dict(COUPLE["bride"], birth_date="2024-03-10", birth_time="02:30:00", timezone="America/New_York"))
        with self.assertRaises(service.ServiceError) as raised:
            service.build(gap, NOW)
        self.assertEqual(raised.exception.status_code, 422)


@unittest.skipUnless(ASTRONOMY, "astronomy-engine is not installed")
class UnlockTests(unittest.TestCase):
    def setUp(self):
        self.key = service.report_key(COUPLE, "unit-secret")
        self.order = {"id": "order_test", "amount": 9900, "currency": "INR",
                      "notes": {"rightconnect_product": "kattam_report", "rightconnect_origin": "https://dev.example", "report_key": self.key}}
        self.entity = {"id": "pay_test", "order_id": "order_test", "amount": 9900, "currency": "INR", "status": "captured"}
        self.proof = {"razorpay_order_id": "order_test", "razorpay_payment_id": "pay_test",
                      "razorpay_signature": hmac.new(b"unit-secret", b"order_test|pay_test", hashlib.sha256).hexdigest()}

    def unlock(self, responses, data=None, proof=None):
        api = AsyncMock(side_effect=responses)
        result = asyncio.run(service.unlock(dict(data or COUPLE, payment=proof or self.proof), SETTINGS, api, NOW))
        return result, api

    def test_order_carries_price_product_and_birth_bound_key_without_birth_data(self):
        api = AsyncMock(return_value={"id": "order_test", "amount": 9900, "currency": "INR"})
        result = asyncio.run(service.create_order(COUPLE, SETTINGS, api))
        payload = api.call_args.args[2]
        self.assertEqual(payload["amount"], 9900)
        self.assertEqual(payload["notes"]["report_key"], self.key)
        self.assertNotIn("1996", json.dumps(payload))
        self.assertLessEqual(len(payload["receipt"]), 40)
        self.assertNotIn("unit-secret", json.dumps(result))

    def test_order_unavailable_without_keys_or_price(self):
        for change in ({"razorpay_key_secret": ""}, {"razorpay_kattam_report_amount_paise": 99}):
            api = AsyncMock()
            with self.assertRaises(service.ServiceError) as raised:
                asyncio.run(service.create_order(COUPLE, SimpleNamespace(**{**vars(SETTINGS), **change}), api))
            self.assertEqual(raised.exception.status_code, 503)
            api.assert_not_awaited()

    def test_captured_payment_returns_full_report(self):
        result, _ = self.unlock([self.order, self.entity])
        self.assertEqual(result["status"], "paid")
        self.assertFalse(result["report"]["locked"])
        self.assertEqual(result["report"]["sections"][-2]["key"], "summary")

    def test_invalid_signature_never_calls_provider(self):
        with self.assertRaises(service.ServiceError) as raised:
            self.unlock([], proof=dict(self.proof, razorpay_signature="invalid"))
        self.assertEqual(raised.exception.status_code, 400)

    def test_payment_for_other_birth_details_or_product_is_rejected(self):
        other = dict(COUPLE, groom=dict(COUPLE["groom"], birth_time="21:16:00"))
        for order, data in ((self.order, other), (dict(self.order, notes={"rightconnect_payment_id": "plan"}), None),
                            (dict(self.order, notes=dict(self.order["notes"], rightconnect_origin="https://prod.example")), None),
                            (dict(self.order, currency="USD"), None)):
            with self.assertRaises(service.ServiceError) as raised:
                self.unlock([order, self.entity], data=data)
            self.assertEqual(raised.exception.status_code, 400)
        with self.assertRaises(service.ServiceError):
            self.unlock([self.order, dict(self.entity, amount=100)])

    def test_names_and_language_can_change_after_payment(self):
        renamed = dict(COUPLE, language="en", bride=dict(COUPLE["bride"], name="Priya R"))
        result, _ = self.unlock([self.order, self.entity], data=renamed)
        self.assertEqual(result["report"]["names"]["bride"], "Priya R")

    def test_authorized_payment_stays_locked(self):
        result, _ = self.unlock([self.order, dict(self.entity, status="authorized")])
        self.assertEqual(result["status"], "pending")
        self.assertNotIn("report", result)


@unittest.skipUnless(ASTRONOMY, "astronomy-engine is not installed")
class JathagamTests(unittest.TestCase):
    PERSON = {"language": "ta", "person": COUPLE["bride"]}

    @classmethod
    def setUpClass(cls):
        cls.full = service.build(cls.PERSON, NOW, "jathagam")
        cls.preview = report.preview(cls.full, "ta")

    def test_sections_show_kattam_first_then_reading(self):
        self.assertEqual([s["key"] for s in self.full["sections"]],
                         ["basic", "charts", "dosha", "planets", "dasa", "timeline", "life", "bhukti", "summary", "expert"])
        self.assertEqual(self.preview["paywall_after"], "charts")
        self.assertEqual(self.full["subtitle"], "Priya")

    def test_charts_are_free_and_paid_text_stays_on_server(self):
        sections = {s["key"]: s for s in self.preview["sections"]}
        full = {s["key"]: s for s in self.full["sections"]}
        self.assertEqual(sections["charts"]["blocks"], full["charts"]["blocks"])
        self.assertTrue(all(cell["planets"] is not None for cell in sections["charts"]["blocks"][0]["charts"][0]["cells"]))
        visible = set(strings(self.preview))
        self.assertFalse(set(full["summary"]["blocks"][0]["lines"]) & visible)
        life = {p for entry in full["life"]["blocks"][0]["items"] for p in entry["paragraphs"][1:]}
        self.assertFalse(life & visible)

    def test_payment_for_a_couple_cannot_unlock_a_horoscope(self):
        self.assertNotEqual(service.report_key(self.PERSON, "s", "jathagam"), service.report_key(COUPLE, "s"))
        self.assertNotEqual(service.couple_key(self.PERSON, "jathagam"), service.couple_key(COUPLE))
        order = {"id": "order_test", "amount": 9900, "currency": "INR",
                 "notes": {"rightconnect_product": "kattam_report", "rightconnect_origin": "https://dev.example",
                           "report_key": service.report_key(self.PERSON, "unit-secret", "jathagam")}}
        proof = {"razorpay_order_id": "order_test", "razorpay_payment_id": "pay_test",
                 "razorpay_signature": hmac.new(b"unit-secret", b"order_test|pay_test", hashlib.sha256).hexdigest()}
        with self.assertRaises(service.ServiceError):
            asyncio.run(service.unlock(dict(self.PERSON, payment=proof), SETTINGS, AsyncMock(side_effect=[order]), NOW, "jathagam"))
        order["notes"]["rightconnect_product"] = "jathagam_report"
        entity = {"id": "pay_test", "order_id": "order_test", "amount": 9900, "currency": "INR", "status": "captured"}
        result = asyncio.run(service.unlock(dict(self.PERSON, payment=proof), SETTINGS, AsyncMock(side_effect=[order, entity]), NOW, "jathagam"))
        self.assertEqual(result["report"]["kind"], "jathagam")

    def test_stored_inputs_keep_only_the_person(self):
        self.assertEqual(service.stored_inputs(self.PERSON, "jathagam"), {"person": COUPLE["bride"]})


@unittest.skipUnless(ASTRONOMY, "astronomy-engine is not installed")
class AccountHelperTests(unittest.TestCase):
    def test_couple_key_ignores_names_language_and_selection(self):
        renamed = dict(COUPLE, language="en", selected={"bride": {"rasi": 0, "nakshatra": 0}},
                       bride=dict(COUPLE["bride"], name="Other"))
        self.assertEqual(service.couple_key(COUPLE), service.couple_key(renamed))
        moved = dict(COUPLE, bride=dict(COUPLE["bride"], birth_time="06:31:00"))
        self.assertNotEqual(service.couple_key(COUPLE), service.couple_key(moved))
        self.assertEqual(len(service.couple_key(COUPLE)), 48)

    def test_stored_inputs_drop_language(self):
        self.assertEqual(set(service.stored_inputs(COUPLE)), {"bride", "groom", "selected"})

    def test_report_score_feeds_history_summary(self):
        full = service.build(COUPLE, NOW)
        self.assertEqual(full["score"], {"stars": 5, "kattam": 3})

    def test_credits_count_only_paid_unexpired_unused_packs(self):
        from datetime import datetime, timedelta, timezone
        now = datetime(2026, 10, 23, tzinfo=timezone.utc)
        pack = lambda **kw: SimpleNamespace(**{"status": "paid", "expires_at": now + timedelta(days=5), "reports_total": 20, "reports_used": 3, **kw})
        packs = [pack(), pack(status="pending"), pack(expires_at=now - timedelta(seconds=1)), pack(reports_used=20), pack(reports_used=18)]
        self.assertEqual(service.credits_left(packs, now), 17 + 2)

    def test_pack_offer_needs_keys_and_positive_terms(self):
        settings = SimpleNamespace(**vars(SETTINGS), razorpay_porutham_pack_amount_paise=29900, porutham_pack_reports=20, porutham_pack_days=30)
        self.assertEqual(service.pack_offer(settings), {"amount_paise": 29900, "reports": 20, "days": 30, "available": True})
        self.assertFalse(service.pack_offer(SimpleNamespace(**{**vars(settings), "porutham_pack_reports": 0}))["available"])
        self.assertFalse(service.pack_offer(SimpleNamespace(**{**vars(settings), "razorpay_key_secret": ""}))["available"])


if __name__ == "__main__":
    unittest.main()
