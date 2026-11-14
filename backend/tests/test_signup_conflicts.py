"""Isolated regressions for signup duplicate checks (phone/email) using stubbed database boundaries."""
import ast
from enum import StrEnum
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from uuid import uuid4


ROOT = Path(__file__).parents[1]
SERVICE_NAMES = {
    "OnboardingConflictError", "SignupFieldConflictError", "PHONE_TAKEN_MESSAGE", "EMAIL_TAKEN_MESSAGE",
    "phone_registered_to_other", "create_user_profile",
}


class Expression:
    def __getattr__(self, name):
        return lambda *args, **kwargs: Expression()

    def __eq__(self, other):
        return Expression()

    def __ne__(self, other):
        return Expression()

    def __or__(self, other):
        return Expression()


class FakeUser:
    id = Expression()
    auth_user_id = Expression()
    email = Expression()
    phone = Expression()
    deleted_at = Expression()

    def __init__(self, **kwargs):
        self.id = uuid4()
        self.__dict__.update(kwargs)


class Role(StrEnum):
    CUSTOMER = "customer"
    EXPERT = "expert"
    COMPANY_ADMIN = "company_admin"


class FakeIntegrityError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.orig = message


def load_service(namespace):
    path = ROOT / "app/features/auth/service.py"
    tree = ast.parse(path.read_text(), filename=str(path), feature_version=(3, 12))
    selected = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in SERVICE_NAMES:
            selected.append(node)
        elif isinstance(node, ast.Assign) and any(getattr(t, "id", None) in SERVICE_NAMES for t in node.targets):
            selected.append(node)
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        *selected,
    ], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


class SignupConflictTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.auth_id = uuid4()
        self.session = SimpleNamespace(
            scalar=AsyncMock(), add=lambda row: None, flush=AsyncMock(),
            commit=AsyncMock(), rollback=AsyncMock(), refresh=AsyncMock(),
        )
        self.service = load_service({
            "User": FakeUser, "UserRole": Role, "UserResponse": SimpleNamespace,
            "select": lambda *args: Expression(), "active_user_by_auth_id": lambda value: Expression(),
            "IntegrityError": FakeIntegrityError,
        })
        self.payload = SimpleNamespace(
            full_name="Same Name", email="new@example.com", phone="+919876543210", role="customer",
            interest=None, interests=[], city=None,
        )

    async def create(self):
        return await self.service.create_user_profile(self.session, self.auth_id, self.payload)

    async def test_duplicate_phone_gets_clear_error_before_insert(self):
        self.session.scalar.side_effect = [None, None, uuid4()]
        with self.assertRaises(self.service.SignupFieldConflictError) as caught:
            await self.create()
        self.assertEqual(caught.exception.field, "phone")
        self.assertIn("mobile number is already registered", caught.exception.message)
        self.session.commit.assert_not_awaited()

    async def test_email_owned_by_other_login_gets_clear_error(self):
        self.session.scalar.side_effect = [None, uuid4()]
        with self.assertRaises(self.service.SignupFieldConflictError) as caught:
            await self.create()
        self.assertEqual(caught.exception.field, "email")

    async def test_already_onboarded_login_keeps_existing_conflict(self):
        self.session.scalar.side_effect = [FakeUser()]
        with self.assertRaises(self.service.OnboardingConflictError):
            await self.create()

    async def test_same_name_and_free_phone_are_allowed(self):
        self.session.scalar.side_effect = [None, None, None]
        result = await self.create()
        self.assertEqual(result.full_name, "Same Name")
        self.session.commit.assert_awaited_once()

    async def test_race_on_phone_index_maps_to_phone_error(self):
        self.session.scalar.side_effect = [None, None, None]
        self.session.commit.side_effect = FakeIntegrityError('duplicate key value violates unique constraint "users_phone_active_idx"')
        with self.assertRaises(self.service.SignupFieldConflictError) as caught:
            await self.create()
        self.assertEqual(caught.exception.field, "phone")
        self.session.rollback.assert_awaited_once()

    async def test_phone_check_ignores_the_callers_own_number(self):
        self.session.scalar.side_effect = [self.auth_id]
        self.assertFalse(await self.service.phone_registered_to_other(self.session, "+919876543210", self.auth_id))
        self.session.scalar.side_effect = [uuid4()]
        self.assertTrue(await self.service.phone_registered_to_other(self.session, "+919876543210", self.auth_id))


if __name__ == "__main__":
    unittest.main()
