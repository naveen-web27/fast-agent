"""Dependency-free link tests and isolated service/ownership orchestration regressions."""
import ast
from datetime import datetime, timezone
from enum import StrEnum
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock
from uuid import uuid4


ROOT = Path(__file__).parents[1]
LINK_SPEC = importlib.util.spec_from_file_location("showcase_links", ROOT / "app/features/showcases/links.py")
links = importlib.util.module_from_spec(LINK_SPEC)
sys.modules[LINK_SPEC.name] = links
LINK_SPEC.loader.exec_module(links)


class VideoLinksTests(unittest.TestCase):
    def test_supported_links_are_canonical_and_tracking_is_removed(self):
        for value in [
            "https://www.youtube.com/shorts/abcdefghI_1?si=tracking",
            "youtube.com/shorts/abcdefghI_1/",
            "https://m.youtube.com/watch?v=abcdefghI_1&t=20",
            "https://youtu.be/abcdefghI_1?si=tracking",
        ]:
            with self.subTest(value=value):
                video = links.parse_video_link(value)
                self.assertEqual(video.url, "https://www.youtube.com/shorts/abcdefghI_1")
                self.assertEqual(video.platform, "youtube")
                self.assertEqual(video.thumbnail_url, "https://i.ytimg.com/vi/abcdefghI_1/hqdefault.jpg")

    def test_instagram_requires_a_reel_and_manual_cover(self):
        video = links.parse_video_link("https://www.instagram.com/reel/Abc_123-/?igsh=tracking")
        self.assertEqual(video.url, "https://www.instagram.com/reel/Abc_123-/")
        self.assertEqual(video.platform, "instagram")
        self.assertIsNone(video.thumbnail_url)
        with self.assertRaisesRegex(ValueError, "Upload"):
            links.validate_cover_url(None, video, "https://project.supabase.co", uuid4())

    def test_reject_unsafe_and_unsupported_links(self):
        for value in [
            "http://youtube.com/shorts/abcdefghI_1",
            "https://youtube.com.evil.example/shorts/abcdefghI_1",
            "https://evil.youtube.com/shorts/abcdefghI_1",
            "https://youtube.com@127.0.0.1/shorts/abcdefghI_1",
            "https://user@youtube.com/shorts/abcdefghI_1",
            "https://youtube.com:443/shorts/abcdefghI_1",
            "https://youtube.com:bad/shorts/abcdefghI_1",
            "https://youtube.com/shorts/short",
            "https://youtube.com/watch?v=abcdefghI_1&v=abcdefghI_2",
            "https://instagram.com/myprofile",
            "https://instagram.com/p/Abc123",
            "https://instagram.com/reel/Abc123/extra",
            "https://127.0.0.1/video",
            "file:///etc/passwd",
            "javascript:alert(1)",
            "https://youtube.com\\@evil.example/shorts/abcdefghI_1",
            "https://youtube.com/shorts/abc\ndefghI_1",
        ]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                links.parse_video_link(value)

    def test_cover_must_be_generated_or_uploaded_by_current_user(self):
        owner = uuid4()
        video = links.parse_video_link("https://instagram.com/reel/Abc123/")
        base = "https://project.supabase.co"
        image = f"{base}/storage/v1/object/public/profile-images/{owner}/showcase-{uuid4()}.webp"
        self.assertEqual(links.validate_cover_url(image, video, base, owner), image)
        youtube = links.parse_video_link("https://youtu.be/abcdefghI_1")
        self.assertEqual(links.validate_cover_url(None, youtube, base, owner), youtube.thumbnail_url)
        for bad in [
            image.replace(str(owner), str(uuid4())),
            image.replace(".webp", ".svg"),
            image + "?redirect=https://evil.example",
            image.replace("showcase-", "../showcase-"),
            "https://evil.example/cover.png",
            "https://i.ytimg.com/vi/abcdefghI_2/hqdefault.jpg",
        ]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                links.validate_cover_url(bad, video, base, owner)


class Expression:
    """Records SQL expression operations without requiring an installed database driver."""
    def __init__(self, value=""):
        self.value = value
        self.locked = False

    def __getattr__(self, name):
        def operation(*args, **kwargs):
            if name == "with_for_update":
                self.locked = True
            return self
        return operation

    def __eq__(self, other):
        return Expression()

    def __ne__(self, other):
        return Expression()

    def __and__(self, other):
        return Expression()


class Kind(StrEnum):
    EXPERT = "expert"
    COMPANY = "company"


class FakeModel:
    id = Expression()
    profile_id = Expression()
    source_url = Expression()
    display_name = Expression()
    created_at = Expression()
    organization_id = Expression()
    user_id = Expression()
    member_role = Expression()

    def __init__(self, **kwargs):
        self.id = uuid4()
        self.created_at = datetime.now(timezone.utc)
        self.__dict__.update(kwargs)


def load_functions(path, namespace, names=None):
    tree = ast.parse(path.read_text(), filename=str(path), feature_version=(3, 12))
    selected = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and (names is None or node.name in names)
    ]
    module = ast.Module(body=[
        ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
        *selected,
    ], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return SimpleNamespace(**namespace)


class ShowcaseServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.auth_id = uuid4()
        self.profile_id = uuid4()
        self.owner = SimpleNamespace(id=uuid4())
        self.profile = SimpleNamespace(
            id=self.profile_id, user_id=self.owner.id, kind=Kind.EXPERT,
            organization_id=None, deleted_at=None, blocked_at=None, display_name="Test expert",
        )
        self.session = SimpleNamespace(
            scalar=AsyncMock(), execute=AsyncMock(), scalars=AsyncMock(),
            get=AsyncMock(), add=lambda row: None,
            commit=AsyncMock(), refresh=AsyncMock(), delete=AsyncMock(),
        )
        self.paid = AsyncMock(return_value=False)
        namespace = {
            "Profile": FakeModel, "Organization": FakeModel, "User": FakeModel,
            "VideoShowcase": FakeModel, "OrganizationMember": FakeModel,
            "ProfileKind": Kind, "MemberRole": SimpleNamespace(ADMIN=SimpleNamespace(value="admin")),
            "select": lambda *args: Expression(), "func": SimpleNamespace(count=lambda: Expression()),
            "or_": lambda *args: Expression(),
            "active_user_by_auth_id": lambda value: Expression(),
            "profile_plan_active": self.paid,
            "parse_video_link": links.parse_video_link, "validate_cover_url": links.validate_cover_url,
            "ShowcaseOut": SimpleNamespace, "ShowcaseList": SimpleNamespace, "ManagedShowcases": SimpleNamespace,
            "SHOWCASE_LIMIT": {False: 2, True: 10},
        }
        load_functions(ROOT / "app/features/profiles/service.py", namespace, {
            "ProfileNotFoundError", "ProfileAccessError", "_require_manage",
        })
        self.service = load_functions(ROOT / "app/features/showcases/service.py", namespace)
        self.session.scalar.side_effect = [self.owner, None, 0]
        self.session.get.return_value = self.profile
        self.payload = SimpleNamespace(
            source_url="https://youtube.com/shorts/abcdefghI_1", title="My service",
            description="A short introduction.", cover_url=None,
        )

    async def save(self, showcase_id=None):
        return await self.service.save_showcase(
            self.session, self.auth_id, self.profile_id, self.payload,
            "https://project.supabase.co", showcase_id,
        )

    async def test_free_profile_can_publish_and_locks_parent(self):
        result = await self.save()
        self.assertEqual(result.title, self.payload.title)
        self.assertEqual(result.cover_url, "https://i.ytimg.com/vi/abcdefghI_1/hqdefault.jpg")
        self.assertTrue(self.session.execute.call_args_list[0].args[0].locked)
        self.session.commit.assert_awaited_once()

    async def test_free_quota_is_two(self):
        self.session.scalar.side_effect = [self.owner, None, 2]
        with self.assertRaisesRegex(self.service.ShowcaseConflictError, "2 showcases"):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_paid_quota_is_ten_and_allows_tenth(self):
        self.paid.return_value = True
        self.session.scalar.side_effect = [self.owner, None, 9]
        await self.save()
        self.session.commit.assert_awaited_once()
        self.session.commit.reset_mock()
        self.session.scalar.side_effect = [self.owner, None, 10]
        with self.assertRaisesRegex(self.service.ShowcaseConflictError, "10 showcases"):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_non_owner_and_customer_cannot_publish(self):
        self.profile.user_id = uuid4()
        self.session.scalar.side_effect = [self.owner]
        with self.assertRaises(self.service.ProfileAccessError):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_company_admin_allowed_but_staff_denied(self):
        self.profile.kind = Kind.COMPANY
        self.profile.organization_id = uuid4()
        organization = SimpleNamespace(deleted_at=None)
        self.session.get.side_effect = [self.profile, organization]
        self.session.scalar.side_effect = [self.owner, uuid4(), None, 0]
        await self.save()
        self.session.get.side_effect = [self.profile]
        self.session.scalar.side_effect = [self.owner, None]
        with self.assertRaises(self.service.ProfileAccessError):
            await self.save()

    async def test_blocked_or_deleted_profile_cannot_publish(self):
        for field in ("blocked_at", "deleted_at"):
            with self.subTest(field=field):
                self.profile.blocked_at = None
                self.profile.deleted_at = None
                setattr(self.profile, field, datetime.now(timezone.utc))
                self.session.scalar.side_effect = [self.owner]
                with self.assertRaises((self.service.ProfileAccessError, self.service.ProfileNotFoundError)):
                    await self.save()

    async def test_duplicate_link_rejected_without_commit(self):
        self.session.scalar.side_effect = [self.owner, uuid4()]
        with self.assertRaisesRegex(self.service.ShowcaseConflictError, "already published"):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_instagram_cannot_publish_without_cover(self):
        self.payload.source_url = "https://instagram.com/reel/Abc123/"
        self.session.scalar.side_effect = [self.owner]
        with self.assertRaisesRegex(ValueError, "Upload"):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_another_company_admin_can_keep_existing_uploaded_cover(self):
        self.profile.kind = Kind.COMPANY
        self.profile.organization_id = uuid4()
        organization = SimpleNamespace(deleted_at=None)
        row = FakeModel(profile_id=self.profile_id)
        row.cover_url = f"https://project.supabase.co/storage/v1/object/public/profile-images/{uuid4()}/showcase-{uuid4()}.webp"
        self.payload.source_url = "https://instagram.com/reel/Abc123/"
        self.payload.cover_url = row.cover_url
        self.session.get.side_effect = [self.profile, organization, row]
        self.session.scalar.side_effect = [self.owner, uuid4(), None]
        result = await self.save(row.id)
        self.assertEqual(result.cover_url, row.cover_url)
        self.paid.assert_not_awaited()

    async def test_expired_plan_blocks_new_posts_without_removing_existing(self):
        self.paid.return_value = False
        self.session.scalar.side_effect = [self.owner, None, 5]
        with self.assertRaises(self.service.ShowcaseConflictError):
            await self.save()
        self.session.delete.assert_not_awaited()
        self.session.commit.assert_not_awaited()

    async def test_deleted_company_cannot_publish(self):
        self.profile.kind = Kind.COMPANY
        self.profile.organization_id = uuid4()
        self.session.get.side_effect = [
            self.profile, SimpleNamespace(deleted_at=datetime.now(timezone.utc)),
        ]
        self.session.scalar.side_effect = [self.owner, uuid4()]
        with self.assertRaises(self.service.ProfileNotFoundError):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_missing_account_cannot_publish(self):
        self.session.scalar.side_effect = [None]
        with self.assertRaises(self.service.ProfileNotFoundError):
            await self.save()
        self.session.commit.assert_not_awaited()

    async def test_edit_cannot_target_another_profiles_post(self):
        row = FakeModel(profile_id=uuid4())
        self.session.get.side_effect = [self.profile, row]
        self.session.scalar.side_effect = [self.owner]
        with self.assertRaises(self.service.ProfileNotFoundError):
            await self.save(row.id)

    async def test_remove_owned_post_persists(self):
        row = FakeModel(profile_id=self.profile_id)
        self.session.get.side_effect = [self.profile, row]
        self.session.scalar.side_effect = [self.owner]
        await self.service.remove_showcase(self.session, self.auth_id, self.profile_id, row.id)
        self.session.delete.assert_awaited_once_with(row)
        self.session.commit.assert_awaited_once()

    async def test_remove_cannot_target_another_profile(self):
        row = FakeModel(profile_id=uuid4())
        self.session.get.side_effect = [self.profile, row]
        self.session.scalar.side_effect = [self.owner]
        with self.assertRaises(self.service.ProfileNotFoundError):
            await self.service.remove_showcase(self.session, self.auth_id, self.profile_id, row.id)
        self.session.delete.assert_not_awaited()

    async def test_public_page_preserves_output_shape(self):
        row = FakeModel(
            profile_id=self.profile_id, source_url="https://www.youtube.com/shorts/abcdefghI_1",
            title="Demo", description="Demo video", cover_url="https://i.ytimg.com/vi/abcdefghI_1/hqdefault.jpg",
        )
        self.session.scalar.side_effect = [13]
        self.session.execute.return_value = SimpleNamespace(all=lambda: [(row, "Expert name")])
        # Public query expressions refer to additional model columns.
        for name in ("kind", "deleted_at", "blocked_at"):
            setattr(FakeModel, name, Expression())
        result = await self.service.list_showcases(self.session, 2, 12)
        self.assertEqual((result.total, result.page, result.page_size), (13, 2, 12))
        self.assertEqual(result.results[0].provider_name, "Expert name")


if __name__ == "__main__":
    unittest.main()
