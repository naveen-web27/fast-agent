"""Isolated payment regression checks with HTTP and database dependencies stubbed."""
import ast
import hashlib
import hmac
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

from app.features.payments.verification import foreign_origin, matching_payment, valid_payment_signature


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        super().__init__(detail)
        self.status_code = status_code


class Column:
    def __init__(self, name):
        self.name = name

    def __eq__(self, value):
        return self.name, value

    def is_(self, value):
        return self.name, value


class Query:
    def __init__(self, model):
        self.model = model
        self.conditions = ()

    def where(self, *conditions):
        self.conditions = conditions
        return self

    def join(self, *args):
        return self

    def with_for_update(self):
        return self


class Payment(SimpleNamespace):
    razorpay_order_id = Column("razorpay_order_id")
    user_id = Column("user_id")


class Profile:
    id = Column("id")
    user_id = Column("user_id")
    kind = Column("kind")
    deleted_at = Column("deleted_at")


def route_scope():
    source = Path(__file__).parents[1] / "app/features/payments/router.py"
    parsed = ast.parse(source.read_text())
    functions = [node for node in parsed.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for function in functions:
        function.decorator_list = []
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *functions], type_ignores=[])
    scope = {
        "ACCESS_DAYS": 30, "HTTPException": HTTPException, "select": Query,
        "Body": lambda **kwargs: None, "Depends": lambda *args: None,
        "get_current_auth_user_id": None, "get_db": None, "get_settings": None,
        "Payment": Payment, "Profile": Profile, "Organization": type("Organization", (), {}), "User": type("User", (), {}),
        "ProfileKind": SimpleNamespace(EXPERT="expert"), "SubscriptionTier": lambda plan: plan,
        "active_user_by_auth_id": lambda auth_id: ("user", auth_id),
        "uuid": __import__("uuid"), "UUID": UUID, "datetime": datetime,
        "timedelta": timedelta, "timezone": timezone, "hmac": hmac, "hashlib": hashlib,
        "valid_payment_signature": valid_payment_signature, "matching_payment": matching_payment,
        "foreign_origin": foreign_origin, "status": SimpleNamespace(HTTP_400_BAD_REQUEST=400),
    }
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), scope)
    return scope


class PaymentValidationTests(unittest.TestCase):
    def test_signature_uses_stored_order_and_rejects_tampering(self):
        signature = hmac.new(b"unit-secret", b"order_test|pay_test", hashlib.sha256).hexdigest()
        self.assertTrue(valid_payment_signature("order_test", "pay_test", signature, "unit-secret"))
        for order, payment, secret in [("order_other", "pay_test", "unit-secret"), ("order_test", "pay_other", "unit-secret"), ("order_test", "pay_test", "" )]:
            self.assertFalse(valid_payment_signature(order, payment, signature, secret))
        self.assertFalse(valid_payment_signature("order_test", "pay_test", "\u2603", "unit-secret"))

    def test_payment_requires_matching_id_order_amount_currency_and_status(self):
        entity = {"id": "pay_test", "order_id": "order_test", "amount": 100, "currency": "INR", "status": "captured"}
        self.assertTrue(matching_payment(entity, "order_test", 100, "pay_test"))
        for field, value in [("id", "pay_other"), ("order_id", "order_other"), ("amount", 99), ("currency", "USD"), ("status", "failed")]:
            self.assertFalse(matching_payment({**entity, field: value}, "order_test", 100, "pay_test"))

    def test_origin_isolation_and_legacy_notes(self):
        self.assertTrue(foreign_origin({"notes": {"rightconnect_origin": "https://prod.example"}}, "https://dev.example"))
        self.assertFalse(foreign_origin({"notes": {"rightconnect_origin": "https://dev.example"}}, "https://dev.example/"))
        for notes in (None, [], {}, {"unrelated": "value"}):
            self.assertFalse(foreign_origin({"notes": notes}, "https://dev.example"))


class PaymentRouteTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.scope = route_scope()
        self.user = SimpleNamespace(id=uuid4(), full_name="Test Buyer", email="buyer@example.test")
        self.payment = Payment(id=uuid4(), user_id=self.user.id, profile_id=uuid4(), organization_id=None,
                               plan="pro", amount_paise=100, status="pending", razorpay_order_id="order_test",
                               razorpay_payment_id=None, access_expires_at=None)
        self.target = SimpleNamespace(subscription_expires_at=None, subscription_tier="free", deleted_at=None)
        self.session = SimpleNamespace(scalar=AsyncMock(side_effect=[self.user, self.payment]),
                                       get=AsyncMock(return_value=self.target), commit=AsyncMock(), add=lambda payment: None)
        self.settings = SimpleNamespace(razorpay_key_id="rzp_test_unit", razorpay_key_secret="unit-secret",
                                        razorpay_webhook_secret="webhook-unit", razorpay_pro_amount_paise=100,
                                        razorpay_enterprise_amount_paise=100, app_base_url="https://dev.example")
        self.entity = {"id": "pay_test", "order_id": "order_test", "amount": 100, "currency": "INR", "status": "captured"}
        self.scope["razorpay_api"] = AsyncMock(return_value=self.entity)
        self.body = {"razorpay_order_id": "order_test", "razorpay_payment_id": "pay_test",
                     "razorpay_signature": hmac.new(b"unit-secret", b"order_test|pay_test", hashlib.sha256).hexdigest()}

    async def verify(self, body=None):
        return await self.scope["verify_payment"](self.body if body is None else body, uuid4(), self.session, self.settings)

    async def test_missing_fields_are_400_without_database_access(self):
        for body in ({}, {"razorpay_order_id": "order_test"}, {**self.body, "razorpay_signature": 123}):
            with self.assertRaises(HTTPException) as raised:
                await self.verify(body)
            self.assertEqual(raised.exception.status_code, 400)
        self.session.scalar.assert_not_awaited()

    async def test_invalid_signature_never_fetches_or_marks_paid(self):
        with self.assertRaises(HTTPException) as raised:
            await self.verify({**self.body, "razorpay_signature": "invalid"})
        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(self.payment.status, "pending")
        self.scope["razorpay_api"].assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_order_lookup_is_scoped_to_authenticated_owner(self):
        self.session.scalar.side_effect = [self.user, None]
        with self.assertRaises(HTTPException) as raised:
            await self.verify()
        self.assertEqual(raised.exception.status_code, 400)
        query = self.session.scalar.call_args.args[0]
        self.assertIn(("user_id", self.user.id), query.conditions)
        self.assertIn(("razorpay_order_id", "order_test"), query.conditions)
        self.session.commit.assert_not_awaited()

    async def test_captured_payment_activates_expert_once(self):
        result = await self.verify()
        self.assertEqual(result["status"], "paid")
        self.assertEqual(self.target.subscription_tier, "pro")
        expiry = self.target.subscription_expires_at
        self.session.scalar.side_effect = [self.user, self.payment]
        self.scope["razorpay_api"].reset_mock()
        repeated = await self.verify()
        self.assertEqual(repeated, result)
        self.assertEqual(expiry, self.target.subscription_expires_at)
        self.session.commit.assert_awaited_once()
        self.scope["razorpay_api"].assert_not_awaited()

    async def test_authorized_payment_does_not_activate(self):
        self.scope["razorpay_api"].return_value = {**self.entity, "status": "authorized"}
        self.assertEqual((await self.verify())["status"], "pending")
        self.assertEqual(self.payment.status, "pending")
        self.session.commit.assert_not_awaited()

    async def test_wrong_amount_is_rejected(self):
        self.scope["razorpay_api"].return_value = {**self.entity, "amount": 99}
        with self.assertRaises(HTTPException) as raised:
            await self.verify()
        self.assertEqual(raised.exception.status_code, 400)
        self.session.commit.assert_not_awaited()

    async def test_refunded_payment_cannot_reactivate(self):
        self.payment.status = "refunded"
        with self.assertRaises(HTTPException):
            await self.verify()
        self.scope["razorpay_api"].assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_company_renewal_extends_existing_expiry(self):
        self.payment.profile_id = None
        self.payment.organization_id = uuid4()
        self.payment.plan = "enterprise"
        original = datetime.now(timezone.utc) + timedelta(days=10)
        self.target.subscription_expires_at = original
        await self.verify()
        self.assertEqual(self.target.subscription_tier, "enterprise")
        self.assertEqual(self.target.subscription_expires_at, original + timedelta(days=30))
        self.assertIs(self.session.get.call_args.args[0], self.scope["Organization"])

    async def test_deleted_target_is_not_activated(self):
        self.target.deleted_at = datetime.now(timezone.utc)
        with self.assertRaises(HTTPException) as raised:
            await self.verify()
        self.assertEqual(raised.exception.status_code, 409)
        self.session.commit.assert_not_awaited()

    async def test_minimum_amount_is_checked_before_database_access(self):
        self.settings.razorpay_pro_amount_paise = 99
        with self.assertRaises(HTTPException) as raised:
            await self.scope["new_payment"]("pro", uuid4(), self.session, self.settings)
        self.assertEqual(raised.exception.status_code, 400)
        self.session.scalar.assert_not_awaited()

    async def test_create_order_uses_server_price_and_origin_without_secret(self):
        self.session.scalar.side_effect = [self.user, uuid4()]
        self.scope["razorpay_api"].return_value = {"id": "order_test", "amount": 100, "currency": "INR"}
        result = await self.scope["create_order"]("pro", uuid4(), self.session, self.settings)
        payload = self.scope["razorpay_api"].call_args.args[3]
        self.assertEqual(payload["amount"], 100)
        self.assertEqual(payload["notes"]["rightconnect_origin"], "https://dev.example")
        self.assertLessEqual(len(payload["receipt"]), 40)
        self.assertEqual(result["order_id"], "order_test")
        self.assertNotIn("unit-secret", str(result))

    async def webhook(self, event, valid_signature=True):
        import json
        body = json.dumps(event).encode()
        signature = hmac.new(b"webhook-unit", body, hashlib.sha256).hexdigest() if valid_signature else "invalid"
        request = SimpleNamespace(body=AsyncMock(return_value=body), json=AsyncMock(return_value=event),
                                  headers={"x-razorpay-signature": signature})
        return await self.scope["razorpay_webhook"](request, self.session, self.settings)

    def order_event(self, origin="https://dev.example"):
        return {"event": "order.paid", "payload": {
            "order": {"entity": {"id": "order_test", "amount": 100, "amount_paid": 100, "currency": "INR", "status": "paid",
                                  "notes": {"rightconnect_payment_id": str(self.payment.id), "rightconnect_origin": origin}}},
            "payment": {"entity": self.entity},
        }}

    async def test_foreign_webhook_is_ignored_without_database_access(self):
        self.assertEqual(await self.webhook(self.order_event("https://prod.example")), {"status": "ignored"})
        self.session.get.assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_webhook_activates_and_duplicate_does_not_extend(self):
        self.session.get.side_effect = [self.payment, self.target, self.payment]
        event = self.order_event()
        self.assertEqual(await self.webhook(event), {"status": "ok"})
        expiry = self.target.subscription_expires_at
        self.assertEqual(await self.webhook(event), {"status": "ok"})
        self.assertEqual(self.target.subscription_expires_at, expiry)
        self.session.commit.assert_awaited_once()

    async def test_own_webhook_retries_if_record_is_not_ready(self):
        self.session.get.return_value = None
        with self.assertRaises(HTTPException) as raised:
            await self.webhook(self.order_event())
        self.assertEqual(raised.exception.status_code, 503)

    async def test_invalid_webhook_signature_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            await self.webhook(self.order_event(), valid_signature=False)
        self.assertEqual(raised.exception.status_code, 400)
        self.session.get.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()