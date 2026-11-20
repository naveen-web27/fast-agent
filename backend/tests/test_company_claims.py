"""Isolated regressions for unclaimed company listings and ownership claims, using stubbed database boundaries."""
import ast
from datetime import datetime, timedelta, timezone
from enum import StrEnum
import hashlib
import html
import logging
from pathlib import Path
import re
import secrets
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from urllib.parse import urlparse
from uuid import uuid4


ROOT = Path(__file__).parents[1]
SERVICE_NAMES = {
    "CLAIM_OTP_PURPOSE", "OTP_TTL_MINUTES", "OTP_MAX_ATTEMPTS", "CODES_PER_EMAIL_WINDOW", "CODES_PER_LISTING_HOUR",
    "FREE_MAIL_DOMAINS", "ListingNotFoundError", "ListingConflictError", "ClaimEligibilityError", "ClaimCodeError",
    "ClaimRateLimitError", "ClaimNotFoundError", "_hash", "email_matches_listing", "_log", "_notify", "_claimable",
    "_administers_company", "_eligible_claimant", "send_claim_code", "submit_claim", "_pending_claim", "approve_claim",
    "reject_claim",
}


class Expression:
    """Stands in for SQLAlchemy columns/queries: every operation returns another expression."""

    def __getattr__(self, name):
        return lambda *args, **kwargs: Expression()

    def __call__(self, *args, **kwargs):
        return Expression()

    def __eq__(self, other):
        return Expression()

    def __ne__(self, other):
        return Expression()

    def __ge__(self, other):
        return Expression()

    def __sub__(self, other):
        return Expression()

    __hash__ = object.__hash__


class Row(SimpleNamespace):
    """A fake ORM row class whose class attributes behave like columns."""

    id = Expression()
    organization_id = Expression()
    user_id = Expression()
    status = Expression()
    email = Expression()
    purpose = Expression()
    verified_at = Expression()
    created_at = Expression()
    member_role = Expression()
    deleted_at = Expression()


class Organization(Row):
    pass


class Profile(Row):
    pass


class User(Row):
    pass


class OrganizationMember(Row):
    pass


class EmailVerification(Row):
    pass


class OrganizationClaim(Row):
    pass


class AdminAction(Row):
    pass


class ProfileKind(StrEnum):
    EXPERT = "expert"
    COMPANY = "company"


class ClaimStatus(StrEnum):
    UNCLAIMED = "unclaimed"
    CLAIMED = "claimed"


class ClaimReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MemberRole(StrEnum):
    ADMIN = "admin"
    STAFF = "staff"


class EmailNotConfiguredError(Exception):
    pass


class EmailDeliveryError(Exception):
    pass


class FakeIntegrityError(Exception):
    pass


def load_service(namespace):
    path = ROOT / "app/features/claims/service.py"
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


class FakeSession:
    """Records writes; `get` answers from a dict keyed by (model, id); `scalar` replays queued answers."""

    def __init__(self, objects=None, scalars=None, scalar_lists=None):
        self.objects = objects or {}
        self.scalar_answers = list(scalars or [])
        self.scalar_lists = list(scalar_lists or [])
        self.added = []
        self.commit = AsyncMock()
        self.rollback = AsyncMock()
        self.refresh = AsyncMock()

    async def get(self, model, key, **kwargs):
        return self.objects.get((model, key))

    async def scalar(self, statement):
        return self.scalar_answers.pop(0)

    async def scalars(self, statement):
        return SimpleNamespace(all=lambda: self.scalar_lists.pop(0))

    def add(self, row):
        if isinstance(row, OrganizationClaim) and not hasattr(row, "id"):
            row.id = uuid4()
            row.created_at = datetime.now(timezone.utc)
        self.added.append(row)


def code_hash(code):
    return hashlib.sha256(code.encode()).hexdigest()


class CompanyClaimTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.sent = []

        async def send_email(settings, *, to, subject, html):
            self.sent.append({"to": to, "subject": subject, "html": html})

        self.service = load_service({
            "Organization": Organization, "Profile": Profile, "User": User, "OrganizationMember": OrganizationMember,
            "EmailVerification": EmailVerification, "OrganizationClaim": OrganizationClaim, "AdminAction": AdminAction,
            "ProfileKind": ProfileKind, "ClaimStatus": ClaimStatus, "ClaimReviewStatus": ClaimReviewStatus,
            "MemberRole": MemberRole, "EmailNotConfiguredError": EmailNotConfiguredError,
            "EmailDeliveryError": EmailDeliveryError, "IntegrityError": FakeIntegrityError, "send_email": send_email,
            "select": lambda *args: Expression(), "func": Expression(), "active_user_by_auth_id": lambda value: Expression(),
            "datetime": datetime, "timedelta": timedelta, "timezone": timezone, "hashlib": hashlib, "secrets": secrets,
            "html": html, "re": re, "urlparse": urlparse, "logger": logging.getLogger("claims-test"),
            "MyClaimOut": SimpleNamespace,
        })
        self.settings = SimpleNamespace()
        self.user = User(id=uuid4(), email="owner@example.com", full_name="Owner", blocked_at=None, deleted_at=None)
        self.organization = Organization(
            id=uuid4(), name="Sri Murugan Mobiles", claim_status="unclaimed", deleted_at=None,
            contact_email="shop@murugan.in", website_url="https://www.murugan.in", email_domain_verified=False,
        )
        self.profile = Profile(
            id=uuid4(), kind=ProfileKind.COMPANY, organization_id=self.organization.id, deleted_at=None, blocked_at=None,
        )

    def session(self, **kwargs):
        objects = {(Profile, self.profile.id): self.profile, (Organization, self.organization.id): self.organization}
        objects.update(kwargs.pop("objects", {}))
        return FakeSession(objects=objects, **kwargs)

    def payload(self, code="123456", email="Shop@Murugan.in"):
        return SimpleNamespace(profile_id=self.profile.id, email=email, code=code, phone=None, note="I own it")

    def verification(self, code="123456", **overrides):
        values = dict(
            code_hash=code_hash(code), expires_at=datetime.now(timezone.utc) + timedelta(minutes=5), attempts=0,
            verified_at=None,
        )
        values.update(overrides)
        return EmailVerification(**values)

    # ---------- matching ----------

    def test_email_match_rules(self):
        match = self.service.email_matches_listing
        self.assertTrue(match("SHOP@murugan.in", "shop@murugan.in", None))
        self.assertTrue(match("anyone@murugan.in", None, "https://www.murugan.in/contact"))
        self.assertTrue(match("anyone@murugan.in", None, "https://shop.murugan.in"))
        self.assertFalse(match("someone@gmail.com", None, "https://gmail.com"))
        self.assertFalse(match("x@evilmurugan.in", None, "https://murugan.in"))
        self.assertFalse(match("x@murugan.in.evil.com", None, "https://murugan.in"))
        self.assertFalse(match("x@other.in", "shop@murugan.in", None))

    # ---------- submitting a claim ----------

    async def test_valid_code_creates_pending_claim_marked_as_matching(self):
        verification = self.verification()
        session = self.session(scalars=[self.user, None, None, verification])
        result = await self.service.submit_claim(session, uuid4(), self.payload())
        claim = next(row for row in session.added if isinstance(row, OrganizationClaim))
        self.assertEqual(claim.status, "pending")
        self.assertEqual(claim.business_email, "shop@murugan.in")
        self.assertTrue(claim.email_matches_listing)
        self.assertIsNotNone(verification.verified_at)
        self.assertEqual(result.status, "pending")
        session.commit.assert_awaited_once()

    async def test_wrong_code_counts_an_attempt_and_creates_nothing(self):
        verification = self.verification()
        session = self.session(scalars=[self.user, None, None, verification])
        with self.assertRaises(self.service.ClaimCodeError):
            await self.service.submit_claim(session, uuid4(), self.payload(code="000000"))
        self.assertEqual(verification.attempts, 1)
        self.assertFalse(any(isinstance(row, OrganizationClaim) for row in session.added))

    async def test_expired_or_exhausted_code_is_rejected(self):
        for verification in [
            self.verification(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)),
            self.verification(attempts=5),
        ]:
            session = self.session(scalars=[self.user, None, None, verification])
            with self.subTest(verification=verification), self.assertRaises(self.service.ClaimCodeError):
                await self.service.submit_claim(session, uuid4(), self.payload())

    async def test_already_claimed_listing_cannot_be_claimed(self):
        self.organization.claim_status = "claimed"
        with self.assertRaises(self.service.ListingConflictError):
            await self.service.submit_claim(self.session(), uuid4(), self.payload())

    async def test_expert_profile_is_not_claimable(self):
        self.profile.kind = ProfileKind.EXPERT
        with self.assertRaises(self.service.ListingNotFoundError):
            await self.service.submit_claim(self.session(), uuid4(), self.payload())

    async def test_people_who_already_run_a_company_or_have_a_pending_claim_are_refused(self):
        for answers, message in [([self.user, uuid4()], "already run a company"), ([self.user, None, uuid4()], "already waiting")]:
            with self.subTest(message=message), self.assertRaisesRegex(self.service.ClaimEligibilityError, message):
                await self.service.submit_claim(self.session(scalars=answers), uuid4(), self.payload())

    async def test_not_onboarded_user_is_refused(self):
        with self.assertRaisesRegex(self.service.ClaimEligibilityError, "Finish creating"):
            await self.service.submit_claim(self.session(scalars=[None]), uuid4(), self.payload())

    # ---------- sending codes ----------

    async def test_send_code_emails_a_hashed_code(self):
        session = self.session(scalars=[self.user, None, None, 0, 0])
        await self.service.send_claim_code(session, self.settings, uuid4(), self.profile.id, " Shop@Murugan.in ")
        stored = next(row for row in session.added if isinstance(row, EmailVerification))
        self.assertEqual(stored.email, "shop@murugan.in")
        self.assertEqual(stored.purpose, "company_claim")
        code = re.search(r"is <strong>(\d{6})</strong>", self.sent[0]["html"]).group(1)
        self.assertEqual(stored.code_hash, code_hash(code))
        self.assertEqual(self.sent[0]["to"], "shop@murugan.in")

    async def test_send_code_is_rate_limited(self):
        for counts in [(3, 3), (0, 10)]:
            session = self.session(scalars=[self.user, None, None, *counts])
            with self.subTest(counts=counts), self.assertRaises(self.service.ClaimRateLimitError):
                await self.service.send_claim_code(session, self.settings, uuid4(), self.profile.id, "a@b.com")
            self.assertEqual(self.sent, [])

    # ---------- admin review ----------

    def pending_claim(self, **overrides):
        values = dict(id=uuid4(), organization_id=self.organization.id, user_id=self.user.id, status="pending")
        values.update(overrides)
        return OrganizationClaim(**values)

    async def test_approve_makes_claimant_admin_and_closes_other_claims(self):
        claim = self.pending_claim()
        rival = self.pending_claim(user_id=uuid4())
        admin = User(id=uuid4())
        session = self.session(
            objects={(OrganizationClaim, claim.id): claim, (User, self.user.id): self.user},
            scalars=[None],
            scalar_lists=[[rival]],
        )
        await self.service.approve_claim(session, self.settings, admin, claim.id)
        member = next(row for row in session.added if isinstance(row, OrganizationMember))
        self.assertEqual((member.user_id, member.member_role), (self.user.id, "admin"))
        self.assertEqual(self.organization.claim_status, "claimed")
        self.assertIsNotNone(self.organization.claimed_at)
        self.assertTrue(self.organization.email_domain_verified)
        self.assertEqual(claim.status, "approved")
        self.assertEqual(rival.status, "rejected")
        self.assertTrue(any(isinstance(row, AdminAction) for row in session.added))
        self.assertEqual(self.sent[0]["to"], self.user.email)

    async def test_approve_refuses_claimed_business_and_ineligible_claimant(self):
        admin = User(id=uuid4())
        self.organization.claim_status = "claimed"
        claim = self.pending_claim()
        session = self.session(objects={(OrganizationClaim, claim.id): claim})
        with self.assertRaises(self.service.ListingConflictError):
            await self.service.approve_claim(session, self.settings, admin, claim.id)

        self.organization.claim_status = "unclaimed"
        self.user.blocked_at = datetime.now(timezone.utc)
        session = self.session(objects={(OrganizationClaim, claim.id): claim, (User, self.user.id): self.user})
        with self.assertRaises(self.service.ClaimEligibilityError):
            await self.service.approve_claim(session, self.settings, admin, claim.id)
        self.assertEqual(claim.status, "pending")
        session.commit.assert_not_awaited()

    async def test_reviewed_claim_cannot_be_reviewed_again(self):
        claim = self.pending_claim(status="approved")
        session = self.session(objects={(OrganizationClaim, claim.id): claim})
        with self.assertRaises(self.service.ClaimNotFoundError):
            await self.service.reject_claim(session, self.settings, User(id=uuid4()), claim.id, "No proof")

    async def test_reject_records_reason_even_when_email_is_not_configured(self):
        async def failing_send(*args, **kwargs):
            raise EmailNotConfiguredError("missing")

        self.service._notify.__globals__["send_email"] = failing_send
        claim = self.pending_claim()
        session = self.session(objects={(OrganizationClaim, claim.id): claim, (User, self.user.id): self.user})
        await self.service.reject_claim(session, self.settings, User(id=uuid4()), claim.id, "Could not confirm ownership")
        self.assertEqual((claim.status, claim.review_reason), ("rejected", "Could not confirm ownership"))
        session.commit.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
