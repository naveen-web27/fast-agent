"""Isolated regressions for the workforce hub rules (skill verification, availability light, hire permissions, claim codes)."""
import ast
from datetime import date, datetime, timedelta, timezone
from enum import StrEnum
import hashlib
from pathlib import Path
import re
import secrets
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from uuid import uuid4


ROOT = Path(__file__).parents[1]
NAMES = {
    "STALE_AFTER_DAYS", "CLAIM_CODE_DAYS", "CLAIM_CODE_ALPHABET", "WorkerNotFoundError", "WorkerAccessError",
    "WorkerConflictError", "WorkerIdentityError", "effective_availability", "availability_is_stale", "build_skills",
    "hire_action_allowed", "generate_claim_code", "normalize_claim_code", "hash_claim_code", "_now",
    "claim_worker_profile", "hire_action", "_user", "_my_worker",
}


class Availability(StrEnum):
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"


class ExperienceStatus(StrEnum):
    SELF = "self"
    PENDING = "pending"
    VERIFIED = "verified"
    DECLINED = "declined"


class HireStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Expression:
    def __getattr__(self, name):
        return lambda *args, **kwargs: Expression()

    def __call__(self, *args, **kwargs):
        return Expression()

    def __eq__(self, other):
        return Expression()

    __hash__ = object.__hash__


class Row(SimpleNamespace):
    id = Expression()
    user_id = Expression()
    deleted_at = Expression()
    claim_code_hash = Expression()


class WorkerProfile(Row):
    pass


class WorkerHire(Row):
    pass


def load(namespace):
    path = ROOT / "app/features/workers/service.py"
    tree = ast.parse(path.read_text(), filename=str(path), feature_version=(3, 12))
    selected = [
        node for node in tree.body
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in NAMES)
        or (isinstance(node, ast.Assign) and any(getattr(t, "id", None) in NAMES for t in node.targets))
    ]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *selected], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


class Session:
    def __init__(self, scalars=(), objects=None):
        self.answers = list(scalars)
        self.objects = objects or {}
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def scalar(self, statement):
        return self.answers.pop(0)

    async def get(self, model, key, **kwargs):
        return self.objects.get((model, key))


class WorkforceRuleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.profile_out = AsyncMock(side_effect=lambda session, worker, user: worker)
        self.hire_out = AsyncMock(side_effect=lambda session, hire, user, side, orgs: (hire, side))
        self.org_ids = AsyncMock(return_value=set())
        self.svc = load({
            "Availability": Availability, "ExperienceStatus": ExperienceStatus, "HireStatus": HireStatus,
            "SkillOut": SimpleNamespace, "WorkerProfile": WorkerProfile, "WorkerHire": WorkerHire,
            "IntegrityError": type("IntegrityError", (Exception,), {}),
            "select": lambda *args: Expression(), "active_user_by_auth_id": lambda value: Expression(),
            "_my_profile_out": self.profile_out, "_hire_out": self.hire_out, "_admin_org_ids": self.org_ids,
            "date": date, "datetime": datetime, "timedelta": timedelta, "timezone": timezone,
            "hashlib": hashlib, "re": re, "secrets": secrets,
        })

    # ---------- availability light ----------

    def test_busy_worker_is_free_again_after_the_date(self):
        today = date(2026, 11, 21)
        self.assertEqual(self.svc.effective_availability("busy", date(2026, 11, 20), today), "available")
        self.assertEqual(self.svc.effective_availability("busy", date(2026, 11, 21), today), "busy")
        self.assertEqual(self.svc.effective_availability("busy", None, today), "busy")
        self.assertEqual(self.svc.effective_availability("offline", date(2026, 1, 1), today), "offline")

    def test_old_green_light_is_flagged_stale(self):
        now = datetime(2026, 11, 21, tzinfo=timezone.utc)
        self.assertTrue(self.svc.availability_is_stale("available", now - timedelta(days=15), now))
        self.assertFalse(self.svc.availability_is_stale("available", now - timedelta(days=3), now))
        self.assertFalse(self.svc.availability_is_stale("offline", now - timedelta(days=90), now))

    # ---------- skills ----------

    def test_only_verified_companies_confirm_skills(self):
        skills = self.svc.build_skills(
            ["Billing", "cooking"],
            [
                (["Saree draping", "billing"], "verified", True, "Lakshmi Silks"),
                (["Room service"], "verified", False, "New Hotel"),
                (["Driving"], "pending", True, "Fast Cabs"),
                (["Fake skill"], "declined", True, "Somewhere"),
            ],
        )
        by_name = {skill.name.lower(): skill for skill in skills}
        self.assertTrue(by_name["saree draping"].verified)
        self.assertEqual(by_name["billing"].verified_by, ["Lakshmi Silks"])
        self.assertTrue(by_name["billing"].self_declared)
        self.assertFalse(by_name["room service"].verified)
        self.assertFalse(by_name["driving"].verified)
        self.assertNotIn("fake skill", by_name)
        self.assertTrue(all(skill.verified for skill in skills[:2]))
        self.assertFalse(skills[-1].verified)

    def test_same_skill_from_two_employers_lists_both(self):
        skills = self.svc.build_skills([], [(["Cooking"], "verified", True, "Hotel A"), (["cooking"], "verified", True, "Hotel B")])
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].verified_by, ["Hotel A", "Hotel B"])
        self.assertFalse(skills[0].self_declared)

    # ---------- hire permissions ----------

    def test_hire_permissions(self):
        allowed = self.svc.hire_action_allowed
        self.assertTrue(allowed("pending", "employer", "worker", "accept"))
        self.assertFalse(allowed("pending", "employer", "employer", "accept"))
        self.assertTrue(allowed("pending", "worker", "employer", "decline"))
        self.assertTrue(allowed("pending", "employer", "employer", "cancel"))
        self.assertFalse(allowed("pending", "employer", "worker", "cancel"))
        self.assertTrue(allowed("accepted", "employer", "worker", "cancel"))
        self.assertTrue(allowed("accepted", "worker", "employer", "complete"))
        self.assertFalse(allowed("accepted", "employer", "worker", "complete"))
        self.assertFalse(allowed("completed", "employer", "employer", "cancel"))
        self.assertFalse(allowed("declined", "employer", "worker", "accept"))

    async def test_only_participants_can_change_a_hire(self):
        hire = WorkerHire(id=uuid4(), worker_id=uuid4(), employer_user_id=uuid4(), organization_id=None, initiated_by="employer", status="pending")
        stranger = SimpleNamespace(id=uuid4())
        session = Session(scalars=[stranger, None], objects={(WorkerHire, hire.id): hire})
        with self.assertRaises(self.svc.WorkerNotFoundError):
            await self.svc.hire_action(session, uuid4(), hire.id, "accept")
        self.assertEqual(hire.status, "pending")

    async def test_worker_accepts_and_employer_completes(self):
        employer = SimpleNamespace(id=uuid4())
        worker_user = SimpleNamespace(id=uuid4())
        worker = WorkerProfile(id=uuid4(), user_id=worker_user.id)
        hire = WorkerHire(id=uuid4(), worker_id=worker.id, employer_user_id=employer.id, organization_id=None, initiated_by="employer", status="pending", responded_at=None, completed_at=None)
        session = Session(scalars=[worker_user, worker], objects={(WorkerHire, hire.id): hire})
        _, side = await self.svc.hire_action(session, uuid4(), hire.id, "accept")
        self.assertEqual((hire.status, side), ("accepted", "worker"))
        self.assertIsNotNone(hire.responded_at)
        session = Session(scalars=[worker_user, worker], objects={(WorkerHire, hire.id): hire})
        with self.assertRaises(self.svc.WorkerConflictError):
            await self.svc.hire_action(session, uuid4(), hire.id, "complete")
        session = Session(scalars=[employer, None], objects={(WorkerHire, hire.id): hire})
        await self.svc.hire_action(session, uuid4(), hire.id, "complete")
        self.assertEqual(hire.status, "completed")
        self.assertIsNotNone(hire.completed_at)

    async def test_company_admin_can_answer_a_job_application(self):
        org_id = uuid4()
        self.org_ids.return_value = {org_id}
        admin = SimpleNamespace(id=uuid4())
        hire = WorkerHire(id=uuid4(), worker_id=uuid4(), employer_user_id=uuid4(), organization_id=org_id, initiated_by="worker", status="pending", responded_at=None)
        session = Session(scalars=[admin, None], objects={(WorkerHire, hire.id): hire})
        await self.svc.hire_action(session, uuid4(), hire.id, "accept")
        self.assertEqual(hire.status, "accepted")

    # ---------- claim codes ----------

    def test_claim_codes_are_readable_and_forgiving(self):
        code = self.svc.generate_claim_code()
        self.assertRegex(code, r"^[A-Z2-9]{4}-[A-Z2-9]{4}$")
        self.assertFalse(set(code) & set("01IOL"))
        self.assertEqual(self.svc.hash_claim_code(code), self.svc.hash_claim_code(f" {code.lower().replace('-', ' ')} "))

    async def test_claim_takes_over_an_unclaimed_profile_once(self):
        user = SimpleNamespace(id=uuid4(), full_name="Murugan K", phone="+919876543210")
        worker = WorkerProfile(
            id=uuid4(), user_id=None, display_name="Murugan", contact_phone=None, claim_status="unclaimed",
            claim_code_hash="x", claim_code_expires_at=datetime.now(timezone.utc) + timedelta(days=1), claimed_at=None,
        )
        result = await self.svc.claim_worker_profile(Session(scalars=[user, None, worker]), uuid4(), "ABCD-2345")
        self.assertIs(result, worker)
        self.assertEqual((worker.user_id, worker.claim_status, worker.display_name), (user.id, "claimed", "Murugan K"))
        self.assertIsNone(worker.claim_code_hash)
        self.assertEqual(worker.contact_phone, user.phone)

    async def test_claim_rejects_expired_used_or_duplicate(self):
        user = SimpleNamespace(id=uuid4(), full_name="A", phone=None)
        expired = WorkerProfile(user_id=None, claim_code_expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))
        used = WorkerProfile(user_id=uuid4(), claim_code_expires_at=datetime.now(timezone.utc) + timedelta(days=1))
        for answers in ([user, None, expired], [user, None, used], [user, None, None]):
            with self.subTest(answers=answers), self.assertRaises(self.svc.WorkerConflictError):
                await self.svc.claim_worker_profile(Session(scalars=answers), uuid4(), "ABCD-2345")
        with self.assertRaisesRegex(self.svc.WorkerConflictError, "already have"):
            await self.svc.claim_worker_profile(Session(scalars=[user, WorkerProfile()]), uuid4(), "ABCD-2345")


if __name__ == "__main__":
    unittest.main()
