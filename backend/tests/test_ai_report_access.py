"""Dependency-free security tests and isolated generation orchestration checks."""
import ast
import asyncio
import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4


SPEC = importlib.util.spec_from_file_location(
    "ai_report_access", Path(__file__).parents[1] / "app/features/ai_reports/access.py"
)
access = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(access)


class CapabilityTests(unittest.TestCase):
    def test_browser_capability(self):
        token = secrets.token_urlsafe(32)
        digest = access.capability_hash(token)
        self.assertEqual(len(digest), 64)
        self.assertNotEqual(digest, token)
        self.assertTrue(access.can_access(None, None, digest, token))
        self.assertFalse(access.can_access(None, None, digest, secrets.token_urlsafe(32)))

    def test_reject_malformed_tokens(self):
        for token in ("", "a" * 42, "a" * 44, "+" * 43, "A" * 42 + "B", " " + "A" * 43, None):
            with self.subTest(token=token), self.assertRaises(ValueError):
                access.capability_hash(token)

    def test_owner_requires_uuid(self):
        owner = uuid4()
        self.assertTrue(access.can_access(owner, owner, "", None))
        self.assertFalse(access.can_access(owner, uuid4(), "", None))
        self.assertFalse(access.can_access(None, None, "", None))
        self.assertFalse(access.can_access(str(owner), str(owner), "", None))

    def test_public_error_is_allowlisted(self):
        self.assertEqual(access.safe_error_code("writer_timeout"), "writer_timeout")
        self.assertEqual(access.safe_error_code("secret provider payload"), "generation_failed")
        self.assertEqual(access.safe_error_code(None), "generation_failed")

    def test_rate_hash_requires_salt(self):
        with self.assertRaises(ValueError):
            access.client_hash("", "127.0.0.1")
        self.assertEqual(access.client_hash("test-salt", "127.0.0.1"), access.client_hash("test-salt", "127.0.0.1"))
        self.assertNotEqual(access.client_hash("test-salt", "127.0.0.1"), access.client_hash("test-salt", "127.0.0.2"))

    def test_rate_salt_separates_deployments(self):
        self.assertNotEqual(access.client_hash("dev-salt", "127.0.0.1"), access.client_hash("prod-salt", "127.0.0.1"))


class FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail


class FakeWriterError(Exception):
    pass


def isolated_functions(filename, names, namespace):
    source = Path(__file__).parents[1] / "app/features/ai_reports" / filename
    tree = ast.parse(source.read_text(), filename=str(source), feature_version=(3, 12))
    selected = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *selected], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
    return SimpleNamespace(**{name: namespace[name] for name in names})


class GenerationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.report = SimpleNamespace(
            id=uuid4(), generation_attempt=2, language="ta", inputs={"private": "input"},
            calculated_data={"frozen_date": "2026-10-16"}, variants={},
        )
        self.session = SimpleNamespace(rollback=AsyncMock())
        self.written = SimpleNamespace(model_dump=lambda **kwargs: {"title": "Written", "sections": []})
        self.module = SimpleNamespace(
            calculate=Mock(), input_schema=SimpleNamespace(model_validate=Mock(return_value="validated")),
            generate_report=AsyncMock(return_value=self.written),
        )
        self.write = AsyncMock(return_value=self.report)
        self.threadpool = AsyncMock(return_value={"calculated": True})
        self.scope = {
            "asyncio": asyncio, "HTTPException": FakeHTTPException,
            "WrittenReport": SimpleNamespace(model_validate=lambda value: value),
            "writer_module": lambda: SimpleNamespace(ReportWriterError=FakeWriterError),
            "run_in_threadpool": self.threadpool, "_guarded_write": self.write,
            "report_output": lambda report: {"id": str(report.id)},
            "json": __import__("json"),
        }
        self.functions = isolated_functions("service.py", {"generate"}, self.scope)

    async def test_existing_calculation_is_never_recalculated(self):
        output = await self.functions.generate(self.session, self.report, self.module, None)
        self.threadpool.assert_not_awaited()
        self.module.calculate.assert_not_called()
        self.module.generate_report.assert_awaited_once_with(self.report.calculated_data, "ta")
        self.assertEqual(output["id"], str(self.report.id))
        self.assertEqual(self.write.await_args.kwargs["status"], "completed")

    async def test_calculation_is_saved_before_writer(self):
        self.report.calculated_data = None

        async def check_saved(calculated, language):
            self.assertEqual(self.write.await_count, 1)
            self.assertEqual(self.write.await_args.kwargs["calculated_data"], calculated)
            return self.written

        self.module.generate_report.side_effect = check_saved
        await self.functions.generate(self.session, self.report, self.module, None)
        self.threadpool.assert_awaited_once_with(self.module.calculate, "validated")
        self.assertEqual(self.write.await_count, 2)

    async def test_writer_failure_does_not_persist_exception_details(self):
        self.module.generate_report.side_effect = FakeWriterError("secret inputs and provider error")
        await self.functions.generate(self.session, self.report, self.module, None)
        self.session.rollback.assert_awaited_once()
        self.assertEqual(self.write.await_args.kwargs, {"status": "failed", "error_code": "writer_failed"})

    async def test_timeout_has_safe_error_code(self):
        self.module.generate_report.side_effect = TimeoutError("private timeout payload")
        await self.functions.generate(self.session, self.report, self.module, None)
        self.assertEqual(self.write.await_args.kwargs["error_code"], "writer_timeout")

    async def test_calculation_failure_is_retrievable(self):
        self.report.calculated_data = None
        self.threadpool.side_effect = ValueError("private birth data")
        output = await self.functions.generate(self.session, self.report, self.module, None)
        self.module.generate_report.assert_not_awaited()
        self.assertEqual(output["id"], str(self.report.id))
        self.assertEqual(self.write.await_args.kwargs["error_code"], "calculation_failed")

    async def test_superseded_calculation_never_reaches_writer(self):
        self.report.calculated_data = None
        self.write.return_value = None
        with self.assertRaises(FakeHTTPException) as failure:
            await self.functions.generate(self.session, self.report, self.module, None)
        self.assertEqual(failure.exception.status_code, 409)
        self.module.generate_report.assert_not_awaited()
        self.assertEqual(self.write.await_args.args[2], 2)

    async def test_superseded_writer_returns_conflict(self):
        self.write.return_value = None
        with self.assertRaises(FakeHTTPException) as failure:
            await self.functions.generate(self.session, self.report, self.module, None)
        self.assertEqual(failure.exception.status_code, 409)
        self.assertEqual(self.write.await_count, 1)


class AvailabilityTests(unittest.TestCase):
    def test_disabled_unconfigured_and_ready(self):
        writer = Mock(return_value=SimpleNamespace(available=lambda: True))
        functions = isolated_functions("service.py", {"ai_available"}, {"writer_module": writer})
        self.assertFalse(functions.ai_available(SimpleNamespace(ai_reports_enabled=False, ai_report_rate_salt="salt")))
        writer.assert_not_called()
        self.assertFalse(functions.ai_available(SimpleNamespace(ai_reports_enabled=True, ai_report_rate_salt="")))
        self.assertTrue(functions.ai_available(SimpleNamespace(ai_reports_enabled=True, ai_report_rate_salt="salt")))
        writer.return_value = SimpleNamespace(available=lambda: False)
        self.assertFalse(functions.ai_available(SimpleNamespace(ai_reports_enabled=True, ai_report_rate_salt="salt")))
        writer.side_effect = ImportError("writer not installed")
        self.assertFalse(functions.ai_available(SimpleNamespace(ai_reports_enabled=True, ai_report_rate_salt="salt")))


class FakeColumn:
    def __eq__(self, value):
        return ("equals", value)

    def __ne__(self, value):
        return ("not_equals", value)

    def __lt__(self, value):
        return ("less_than", value)

    def __add__(self, value):
        return ("add", value)


class ClaimTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.report = SimpleNamespace(
            id=uuid4(), status="completed", last_attempt_at=self.now,
            generation_attempt=1, attempt_count=1, calculated_data={"frozen": True},
            variants={"ta": {"title": "Cached"}}, token_hash="0" * 64,
            service_type="horoscope",
        )
        self.statement = Mock()
        for name in ("where", "values", "returning", "execution_options"):
            getattr(self.statement, name).return_value = self.statement
        self.session = SimpleNamespace(
            execute=AsyncMock(return_value=SimpleNamespace(scalar_one_or_none=lambda: self.report)),
            commit=AsyncMock(), rollback=AsyncMock(),
        )
        self.budget = AsyncMock()
        self.generate = AsyncMock(return_value={"status": "completed"})
        model = SimpleNamespace(**{name: FakeColumn() for name in (
            "id", "generation_attempt", "attempt_count", "status", "last_attempt_at"
        )})
        namespace = {
            "authorized_report": AsyncMock(return_value=self.report),
            "require_service": Mock(return_value="module"), "now_utc": lambda: self.now,
            "STALE_AFTER": timedelta(minutes=5), "MAX_ATTEMPTS": 5,
            "HTTPException": FakeHTTPException, "AIReport": model,
            "update": lambda model: self.statement, "or_": lambda *conditions: conditions,
            "consume_budget": self.budget, "generate": self.generate,
            "report_output": lambda report: {"id": str(report.id)}, "json": __import__("json"),
        }
        self.functions = isolated_functions("service.py", {"change_report"}, namespace)

    async def change(self, language="ta", **kwargs):
        return await self.functions.change_report(
            self.session, self.report.id, language, None, None, "127.0.0.1", None, **kwargs
        )

    async def test_cached_language_has_no_external_call_or_budget(self):
        await self.change(translation=True)
        self.generate.assert_not_awaited()
        self.budget.assert_not_awaited()
        self.session.commit.assert_awaited_once()

    async def test_pending_is_busy_even_with_cached_variant(self):
        self.report.status = "pending"
        with self.assertRaises(FakeHTTPException) as failure:
            await self.change()
        self.assertEqual(failure.exception.status_code, 409)
        self.session.execute.assert_not_awaited()
        self.generate.assert_not_awaited()

    async def test_attempt_limit_prevents_generation(self):
        self.report.attempt_count = 5
        with self.assertRaises(FakeHTTPException) as failure:
            await self.change("en")
        self.assertEqual(failure.exception.status_code, 429)
        self.session.execute.assert_not_awaited()

    async def test_translation_without_saved_calculation_never_recalculates(self):
        self.report.status = "failed"
        self.report.calculated_data = None
        with self.assertRaises(FakeHTTPException) as failure:
            await self.change("en", translation=True)
        self.assertEqual(failure.exception.status_code, 409)
        self.generate.assert_not_awaited()

    async def test_stale_pending_can_be_reclaimed_and_committed(self):
        self.report.status = "pending"
        self.report.last_attempt_at = self.now - timedelta(minutes=6)

        async def check_committed(*args):
            self.session.commit.assert_awaited_once()
            self.budget.assert_awaited_once()
            return {"status": "completed"}

        self.generate.side_effect = check_committed
        await self.change("en")
        values = self.statement.values.call_args.kwargs
        self.assertEqual(values["generation_attempt"], ("add", 1))
        self.assertEqual(values["attempt_count"], ("add", 1))
        self.assertEqual(values["status"], "pending")

    async def test_lost_claim_does_not_consume_budget(self):
        self.session.execute.return_value = SimpleNamespace(scalar_one_or_none=lambda: None)
        with self.assertRaises(FakeHTTPException) as failure:
            await self.change("en")
        self.assertEqual(failure.exception.status_code, 409)
        self.session.rollback.assert_awaited_once()
        self.budget.assert_not_awaited()
        self.generate.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()