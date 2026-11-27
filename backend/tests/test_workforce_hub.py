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
    "claim_worker_profile", "hire_action", "_user", "_my_worker", "pay_fields",
    "worker_contact", "apply_hire_action", "generate_link_key", "hash_link_key", "reachable", "LINK_INVALID",
    "_link_worker", "link_hire_action", "attach_worker", "link_connect_account",
    "INDIA_TIME", "WorkerLimitError", "india_day_start", "contact_limit_message", "merge_profile_fields", "opened_today",
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

    def __ge__(self, other):
        return Expression()

    def __add__(self, other):
        return Expression()

    __hash__ = object.__hash__


class Row(SimpleNamespace):
    id = Expression()
    user_id = Expression()
    deleted_at = Expression()
    claim_code_hash = Expression()
    access_key_hash = Expression()


class WorkerProfile(Row):
    pass


class WorkerHire(Row):
    pass


class WorkerContactView(Row):
    worker_id = Expression()
    viewer_user_id = Expression()
    first_viewed_at = Expression()


class ProfileContactView(Row):
    profile_id = Expression()
    viewer_user_id = Expression()
    first_viewed_at = Expression()


class SubscriptionTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


CONTACT_DAILY_LIMIT = {SubscriptionTier.FREE: 10, SubscriptionTier.PRO: 20, SubscriptionTier.ENTERPRISE: 30}


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
        self.added = []

    def add(self, row):
        self.added.append(row)

    async def scalar(self, statement):
        return self.answers.pop(0)

    async def get(self, model, key, **kwargs):
        return self.objects.get((model, key))


class WorkforceRuleTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.profile_out = AsyncMock(side_effect=lambda session, worker, user: worker)
        self.hire_out = AsyncMock(side_effect=lambda session, hire, user, side, orgs: (hire, side))
        self.org_ids = AsyncMock(return_value=set())
        self.contact_limit = AsyncMock(return_value=10)
        self.svc = load({
            "WorkerContactView": WorkerContactView, "ProfileContactView": ProfileContactView, "SubscriptionTier": SubscriptionTier,
            "CONTACT_DAILY_LIMIT": CONTACT_DAILY_LIMIT, "contact_daily_limit": self.contact_limit, "func": Expression(),
            "Availability": Availability, "ExperienceStatus": ExperienceStatus, "HireStatus": HireStatus,
            "SkillOut": SimpleNamespace, "WorkerProfile": WorkerProfile, "WorkerHire": WorkerHire,
            "IntegrityError": type("IntegrityError", (Exception,), {}),
            "select": lambda *args: Expression(), "active_user_by_auth_id": lambda value: Expression(),
            "_my_profile_out": self.profile_out, "_hire_out": self.hire_out, "_admin_org_ids": self.org_ids,
            "_visible_worker": AsyncMock(), "_link_profile_out": AsyncMock(side_effect=lambda session, worker: worker), "DirectContact": SimpleNamespace, "User": Row,
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

    # ---------- pay range ----------

    def test_hidden_pay_is_only_shown_to_the_worker(self):
        worker = SimpleNamespace(rate_amount=500, rate_max=1000, rate_unit="day", rate_hidden=True)
        self.assertEqual(
            self.svc.pay_fields(worker, include_private=False),
            {"rate_amount": None, "rate_max": None, "rate_unit": None, "rate_hidden": True},
        )
        self.assertEqual(
            self.svc.pay_fields(worker, include_private=True),
            {"rate_amount": 500, "rate_max": 1000, "rate_unit": "day", "rate_hidden": True},
        )

    def test_visible_pay_range_is_public(self):
        worker = SimpleNamespace(rate_amount=500, rate_max=1000, rate_unit="day", rate_hidden=False)
        self.assertEqual(self.svc.pay_fields(worker, include_private=False)["rate_max"], 1000)

    # ---------- direct contact ----------

    async def test_contact_needs_the_workers_permission(self):
        owner = SimpleNamespace(id=uuid4(), phone="+919876543210", email="a@b.in")
        worker = WorkerProfile(user_id=owner.id, show_contact=False)
        self.svc.worker_contact.__globals__["_visible_worker"].return_value = worker
        with self.assertRaises(self.svc.WorkerAccessError):
            await self.svc.worker_contact(Session(scalars=[SimpleNamespace(id=uuid4())]), uuid4(), uuid4())
        no_number = WorkerProfile(user_id=None, show_contact=True, contact_phone=None, contact_email=None)
        self.svc.worker_contact.__globals__["_visible_worker"].return_value = no_number
        with self.assertRaises(self.svc.WorkerNotFoundError):
            await self.svc.worker_contact(Session(scalars=[SimpleNamespace(id=uuid4())]), uuid4(), uuid4())

    async def test_contact_falls_back_to_the_account_phone_and_email(self):
        owner = SimpleNamespace(id=uuid4(), phone="+919876543210", email="fascino@gmail.com")
        worker = WorkerProfile(id=uuid4(), user_id=owner.id, show_contact=True, contact_phone=None, contact_email=None, display_name="Fascino")
        self.svc.worker_contact.__globals__["_visible_worker"].return_value = worker
        contact = await self.svc.worker_contact(Session(scalars=[SimpleNamespace(id=uuid4()), None, None, 0], objects={(Row, owner.id): owner}), uuid4(), uuid4())
        self.assertEqual((contact.name, contact.phone, contact.email), ("Fascino", "+919876543210", "fascino@gmail.com"))
        worker.contact_phone = "+919000000001"
        contact = await self.svc.worker_contact(Session(scalars=[SimpleNamespace(id=uuid4()), None, None, 0], objects={(Row, owner.id): owner}), uuid4(), uuid4())
        self.assertEqual(contact.phone, "+919000000001")

    async def test_admin_added_worker_contact_is_visible_and_logged(self):
        worker = WorkerProfile(id=uuid4(), user_id=None, access_key_hash=None, show_contact=True,
                               contact_phone="+919000000002", contact_email="ravi@gmail.com", display_name="Ravi")
        self.svc.worker_contact.__globals__["_visible_worker"].return_value = worker
        viewer = SimpleNamespace(id=uuid4())
        session = Session(scalars=[viewer, None, None, 3])
        contact = await self.svc.worker_contact(session, uuid4(), uuid4())
        self.assertEqual((contact.phone, contact.email, contact.daily_limit, contact.left_today), ("+919000000002", "ravi@gmail.com", 10, 6))
        [view] = session.added
        self.assertEqual((view.worker_id, view.viewer_user_id, view.view_count), (worker.id, viewer.id, 1))
        session.commit.assert_awaited_once()

    async def test_daily_limit_stops_new_contacts_but_not_repeat_views(self):
        worker = WorkerProfile(id=uuid4(), user_id=None, show_contact=True, contact_phone="+919000000003", contact_email=None, display_name="Mani")
        self.svc.worker_contact.__globals__["_visible_worker"].return_value = worker
        with self.assertRaises(self.svc.WorkerLimitError) as caught:
            await self.svc.worker_contact(Session(scalars=[SimpleNamespace(id=uuid4()), None, None, 10]), uuid4(), uuid4())
        self.assertIn("Pro gives 20", str(caught.exception))
        seen = WorkerContactView(view_count=2, last_viewed_at=None)
        session = Session(scalars=[SimpleNamespace(id=uuid4()), None, seen, 10])
        contact = await self.svc.worker_contact(session, uuid4(), uuid4())
        self.assertEqual((seen.view_count, contact.left_today), (3, 0))
        self.assertEqual(session.added, [])
        self.contact_limit.return_value = None
        contact = await self.svc.worker_contact(Session(scalars=[SimpleNamespace(id=uuid4()), None, None, 500]), uuid4(), uuid4())
        self.assertIsNone(contact.left_today)
        self.contact_limit.return_value = 10

    async def test_own_profile_contact_is_not_logged(self):
        me = SimpleNamespace(id=uuid4(), phone="+919876543210", email="me@x.in")
        worker = WorkerProfile(id=uuid4(), user_id=me.id, show_contact=True, contact_phone=None, contact_email=None, display_name="Me")
        self.svc.worker_contact.__globals__["_visible_worker"].return_value = worker
        session = Session(scalars=[me], objects={(Row, me.id): me})
        await self.svc.worker_contact(session, uuid4(), uuid4())
        self.assertEqual(session.added, [])
        session.commit.assert_not_awaited()

    def test_daily_limit_resets_at_midnight_india_time(self):
        start = self.svc.india_day_start(datetime(2026, 11, 22, 19, 0, tzinfo=timezone.utc))
        self.assertEqual(start.astimezone(timezone.utc), datetime(2026, 11, 22, 18, 30, tzinfo=timezone.utc))
        start = self.svc.india_day_start(datetime(2026, 11, 22, 18, 0, tzinfo=timezone.utc))
        self.assertEqual(start.astimezone(timezone.utc), datetime(2026, 11, 21, 18, 30, tzinfo=timezone.utc))

    def test_limit_messages_point_to_the_next_plan(self):
        self.assertIn("Enterprise 30", self.svc.contact_limit_message(10))
        self.assertIn("Enterprise gives 30", self.svc.contact_limit_message(20))
        self.assertNotIn("Plans", self.svc.contact_limit_message(30))

    def test_merge_keeps_the_workers_entries_and_fills_gaps(self):
        target = WorkerProfile(bio=None, city="Salem", area=None, pincode=None, avatar_url=None, contact_email=None, contact_phone="+919000000004",
                               years_experience=2, rate_amount=None, rate_max=None, rate_unit=None, rate_hidden=False,
                               skills=["Cooking"], languages=["Tamil"], review_count=1, average_rating=5, work_mode="onsite", preferred_location=None)
        source = WorkerProfile(bio="Hotel cook", city="Chennai", area="Idappadi", pincode="637101", avatar_url=None, contact_email="c@x.in",
                               contact_phone="+919000000004", years_experience=6, rate_amount=500, rate_max=800, rate_unit="day", rate_hidden=True,
                               skills=["cooking", "Billing"], languages=["Tamil", "English"], review_count=3, average_rating=4,
                               work_mode="hybrid", preferred_location="Salem, Erode")
        self.svc.merge_profile_fields(target, source)
        self.assertEqual((target.bio, target.city, target.area, target.pincode, target.contact_email), ("Hotel cook", "Salem", "Idappadi", "637101", "c@x.in"))
        self.assertEqual((target.work_mode, target.preferred_location), ("onsite", "Salem, Erode"))
        self.assertEqual((target.years_experience, target.rate_amount, target.rate_max, target.rate_unit, target.rate_hidden), (6, 500, 800, "day", True))
        self.assertEqual((target.skills, target.languages), (["Cooking", "Billing"], ["Tamil", "English"]))
        self.assertEqual((target.review_count, target.average_rating), (4, 4.2))

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


    # ---------- personal worker links ----------

    def test_link_keys_are_long_and_only_hashes_are_stored(self):
        key = self.svc.generate_link_key()
        self.assertGreaterEqual(len(key), 24)
        self.assertNotEqual(key, self.svc.generate_link_key())
        self.assertEqual(len(self.svc.hash_link_key(key)), 64)
        self.assertEqual(self.svc.hash_link_key(f" {key} "), self.svc.hash_link_key(key))
        self.assertNotIn(key, self.svc.hash_link_key(key))

    def test_link_makes_a_worker_reachable(self):
        self.assertFalse(self.svc.reachable(WorkerProfile(user_id=None, access_key_hash=None)))
        self.assertTrue(self.svc.reachable(WorkerProfile(user_id=None, access_key_hash="x")))
        self.assertTrue(self.svc.reachable(WorkerProfile(user_id=uuid4(), access_key_hash=None)))

    async def test_bad_or_blocked_link_is_refused(self):
        with self.assertRaises(self.svc.WorkerAccessError):
            await self.svc._link_worker(Session(scalars=[None]), "k" * 24)
        blocked = WorkerProfile(id=uuid4(), blocked_at=datetime.now(timezone.utc))
        with self.assertRaises(self.svc.WorkerAccessError):
            await self.svc._link_worker(Session(scalars=[blocked]), "k" * 24)

    async def test_link_stops_when_connected_account_is_blocked_or_deleted(self):
        owner_id = uuid4()
        worker = WorkerProfile(id=uuid4(), user_id=owner_id, blocked_at=None)
        now = datetime.now(timezone.utc)
        for owner in (Row(deleted_at=None, blocked_at=now), Row(deleted_at=now, blocked_at=None), None):
            session = Session(scalars=[worker], objects={(Row, owner_id): owner} if owner else {})
            with self.assertRaises(self.svc.WorkerAccessError):
                await self.svc._link_worker(session, "k" * 24)
        active = Session(scalars=[worker], objects={(Row, owner_id): Row(deleted_at=None, blocked_at=None)})
        self.assertIs(await self.svc._link_worker(active, "k" * 24), worker)

    async def test_link_can_only_answer_its_own_requests(self):
        worker = WorkerProfile(id=uuid4(), user_id=None, blocked_at=None)
        other = WorkerHire(id=uuid4(), worker_id=uuid4(), initiated_by="employer", status="pending")
        with self.assertRaises(self.svc.WorkerNotFoundError):
            await self.svc.link_hire_action(Session(scalars=[worker], objects={(WorkerHire, other.id): other}), "k" * 24, other.id, "accept")
        self.assertEqual(other.status, "pending")
        mine = WorkerHire(id=uuid4(), worker_id=worker.id, initiated_by="employer", status="pending", responded_at=None)
        await self.svc.link_hire_action(Session(scalars=[worker], objects={(WorkerHire, mine.id): mine}), "k" * 24, mine.id, "accept")
        self.assertEqual(mine.status, "accepted")
        self.assertIsNotNone(mine.responded_at)
        job_application = WorkerHire(id=uuid4(), worker_id=worker.id, initiated_by="worker", status="pending")
        with self.assertRaises(self.svc.WorkerConflictError):
            await self.svc.link_hire_action(Session(scalars=[worker], objects={(WorkerHire, job_application.id): job_application}), "k" * 24, job_application.id, "accept")

    async def test_connecting_google_keeps_the_same_profile(self):
        user = SimpleNamespace(id=uuid4(), phone="+919876543210")
        worker = WorkerProfile(id=uuid4(), user_id=None, blocked_at=None, contact_phone=None, claim_status="unclaimed",
                               claim_code_hash="old", claim_code_expires_at=datetime.now(timezone.utc), access_key_hash="h")
        session = Session(scalars=[user, worker, None])
        result = await self.svc.link_connect_account(session, uuid4(), "k" * 24)
        self.assertIs(result, worker)
        self.assertEqual((worker.user_id, worker.claim_status, worker.contact_phone), (user.id, "claimed", user.phone))
        self.assertIsNone(worker.claim_code_hash)
        self.assertEqual(worker.access_key_hash, "h")
        session.commit.assert_awaited_once()

    async def test_connect_refuses_a_second_profile_or_someone_elses(self):
        user = SimpleNamespace(id=uuid4(), phone=None)
        taken = WorkerProfile(id=uuid4(), user_id=uuid4(), blocked_at=None)
        with self.assertRaises(self.svc.WorkerConflictError):
            await self.svc.link_connect_account(
                Session(scalars=[user, taken], objects={(Row, taken.user_id): Row(deleted_at=None, blocked_at=None)}),
                uuid4(), "k" * 24,
            )
        free = WorkerProfile(id=uuid4(), user_id=None, blocked_at=None)
        own = WorkerProfile(id=uuid4(), user_id=user.id)
        session = Session(scalars=[user, free, own])
        with self.assertRaises(self.svc.WorkerConflictError):
            await self.svc.link_connect_account(session, uuid4(), "k" * 24)
        self.assertIsNone(free.user_id)
        session.commit.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
