"""Short database transactions surrounding isolated calculation and writer work."""
import asyncio
import hashlib
import importlib
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import delete, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.models.ai_report import AIReport, AIReportFamilyMember, AIReportUsage

from .access import ERROR_MESSAGES, can_access, capability_hash, client_hash, safe_error_code
from .astrology import CALCULATION_VERSION
from .contracts import ReportRequest, WrittenReport
from .registry import SERVICES

MAX_ATTEMPTS = 5
STALE_AFTER = timedelta(minutes=5)
ASTRONOMICAL_SERVICES = frozenset({"horoscope", "compatibility", "gemstone", "baby-names", "forecast"})


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def writer_module():
    return importlib.import_module("app.features.ai_reports.writer")


def ai_available(settings: Settings) -> bool:
    if not getattr(settings, "ai_reports_enabled", False) or not getattr(settings, "ai_report_rate_salt", ""):
        return False
    try:
        return bool(writer_module().available())
    except Exception:
        return False


def unavailable_reason(key: str, settings: Settings) -> str | None:
    if not ai_available(settings):
        return "AI reports are not configured or are currently disabled."
    if key in ASTRONOMICAL_SERVICES and importlib.util.find_spec("swisseph") is None:
        return "Astronomical calculations are currently unavailable."
    return None


def require_service(key: str, settings: Settings):
    module = SERVICES.get(key)
    if module is None:
        raise HTTPException(404, "Report service not found")
    reason = unavailable_reason(key, settings)
    if reason:
        raise HTTPException(503, reason)
    return module


def catalogue(settings: Settings) -> dict:
    available = ai_available(settings)
    services = []
    for key, module in SERVICES.items():
        reason = unavailable_reason(key, settings)
        descriptor = {name: getattr(module, name) for name in (
            "key", "title_ta", "title_en", "description_ta", "description_en", "icon"
        )}
        descriptor.update(input_schema=module.input_schema.model_json_schema(), available=reason is None)
        if reason:
            descriptor["unavailable_reason"] = reason
        services.append(descriptor)
    return {"services": services, "ai_available": available}


def retention_cutoff(settings: Settings) -> datetime:
    return now_utc() - timedelta(days=max(1, getattr(settings, "ai_report_retention_days", 30)))


def report_output(report: AIReport) -> dict:
    output = {
        "id": str(report.id), "service_type": report.service_type, "status": report.status,
        "language": report.language, "created_at": report.created_at.isoformat(),
        "updated_at": report.updated_at.isoformat(), "tier": report.tier,
        "report": report.variants.get(report.language) if report.status == "completed" else None,
    }
    if report.status == "failed":
        code = safe_error_code(report.error_code)
        output.update(error_code=code, error=ERROR_MESSAGES[code])
    return output


async def authorized_report(
    session: AsyncSession, report_id: UUID, user_id: UUID | None,
    token: str | None, settings: Settings,
) -> AIReport:
    report = await session.scalar(select(AIReport).where(
        AIReport.id == report_id, AIReport.created_at >= retention_cutoff(settings)
    ).execution_options(populate_existing=True))
    if report is None or not can_access(report.user_id, user_id, report.token_hash, token):
        raise HTTPException(404, "Report not found")
    return report


async def advisory_lock(session: AsyncSession, key: str) -> None:
    lock_id = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big", signed=True)
    await session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": lock_id})


async def consume_budget(session: AsyncSession, settings: Settings, host: str, token_hash: str) -> None:
    salt = getattr(settings, "ai_report_rate_salt", "")
    if not salt:
        raise HTTPException(503, "AI report rate limiting is not configured")
    now = now_utc()
    hour = now.replace(minute=0, second=0, microsecond=0)
    day = hour.replace(hour=0)
    hourly = max(0, getattr(settings, "ai_report_hourly_limit", 5))
    daily = max(0, getattr(settings, "ai_report_daily_limit", 100))
    buckets = [
        (f"global:{day.isoformat()}", daily, day + timedelta(days=1)),
        (f"ip:{client_hash(salt, host)}:{hour.isoformat()}", hourly, hour + timedelta(hours=1)),
        (f"token:{token_hash}:{hour.isoformat()}", hourly, hour + timedelta(hours=1)),
    ]
    try:
        for key, limit, expires in buckets:
            await advisory_lock(session, key)
            statement = insert(AIReportUsage).values(id=key, count=1, expires_at=expires)
            statement = statement.on_conflict_do_update(
                index_elements=[AIReportUsage.id], set_={"count": AIReportUsage.count + 1}
            ).returning(AIReportUsage.count)
            count = await session.scalar(statement)
            if count > limit:
                raise HTTPException(429, "AI report limit reached. Please try again later.")
        expired = select(AIReportUsage.id).where(AIReportUsage.expires_at < now).limit(100)
        await session.execute(delete(AIReportUsage).where(AIReportUsage.id.in_(expired)))
    except BaseException:
        await session.rollback()
        raise


async def _guarded_write(session: AsyncSession, report_id: UUID, attempt: int, **values) -> AIReport | None:
    result = await session.execute(update(AIReport).where(
        AIReport.id == report_id, AIReport.generation_attempt == attempt, AIReport.status == "pending"
    ).values(**values, updated_at=now_utc()).returning(AIReport).execution_options(populate_existing=True))
    report = result.scalar_one_or_none()
    await session.commit()
    return report


async def generate(session: AsyncSession, report: AIReport, module, settings: Settings) -> dict:
    report_id, attempt, language = report.id, report.generation_attempt, report.language
    inputs, calculated, variants = report.inputs, report.calculated_data, dict(report.variants)
    error_code = "calculation_failed"
    try:
        if calculated is None:
            validated = module.input_schema.model_validate(inputs)
            calculated = await run_in_threadpool(module.calculate, validated)
            saved = await _guarded_write(session, report_id, attempt, calculated_data=calculated)
            if saved is None:
                raise HTTPException(409, "A newer report attempt has taken over")
        error_code = "writer_failed"
        writer = writer_module()
        try:
            written = await asyncio.wait_for(module.generate_report(calculated, language), timeout=45)
            written = WrittenReport.model_validate(written)
        except writer.ReportWriterError:
            raise
        content = written.model_dump(mode="json")
        variants[language] = content
        saved = await _guarded_write(
            session, report_id, attempt, variants=variants, ai_report=json.dumps(content, ensure_ascii=False),
            status="completed", error_code=None,
        )
    except HTTPException:
        raise
    except Exception as failure:
        await session.rollback()
        if isinstance(failure, TimeoutError):
            error_code = "writer_timeout"
        saved = await _guarded_write(session, report_id, attempt, status="failed", error_code=error_code)
    if saved is None:
        raise HTTPException(409, "A newer report attempt has taken over")
    return report_output(saved)


async def create_report(
    session: AsyncSession, service_type: str, payload: ReportRequest, token: str,
    user_id: UUID | None, host: str, settings: Settings,
) -> dict:
    module = require_service(service_type, settings)
    try:
        digest = capability_hash(token)
    except ValueError as failure:
        raise HTTPException(422, "A valid X-Report-Token is required") from failure
    try:
        validated = module.input_schema.model_validate(payload.inputs)
    except ValidationError:
        raise HTTPException(422, "Invalid report inputs; check the service input schema") from None
    await consume_budget(session, settings, host, digest)
    report = AIReport(
        service_type=service_type, inputs=validated.model_dump(mode="json"), token_hash=digest,
        user_id=user_id, language=payload.language, tier="basic", engine_version=CALCULATION_VERSION,
        prompt_version=str(getattr(writer_module(), "PROMPT_VERSION", "1.0.0")),
    )
    session.add(report)
    await session.commit()
    return await generate(session, report, module, settings)


async def change_report(
    session: AsyncSession, report_id: UUID, language: str, user_id: UUID | None,
    token: str | None, host: str, settings: Settings, *, translation: bool = False,
) -> dict:
    report = await authorized_report(session, report_id, user_id, token, settings)
    module = require_service(report.service_type, settings)
    now = now_utc()
    if report.status == "pending" and report.last_attempt_at >= now - STALE_AFTER:
        raise HTTPException(409, "Report generation is already in progress")
    if translation and report.calculated_data is None:
        raise HTTPException(409, "Retry the original report before changing its language")
    if language in report.variants:
        result = await session.execute(update(AIReport).where(
            AIReport.id == report_id,
            AIReport.generation_attempt == report.generation_attempt,
            or_(AIReport.status != "pending", AIReport.last_attempt_at < now - STALE_AFTER),
        ).values(language=language, status="completed", error_code=None,
                 ai_report=json.dumps(report.variants[language], ensure_ascii=False), updated_at=now)
            .returning(AIReport).execution_options(populate_existing=True))
        cached = result.scalar_one_or_none()
        await session.commit()
        if cached is None:
            raise HTTPException(409, "Report generation is already in progress")
        return report_output(cached)
    if report.attempt_count >= MAX_ATTEMPTS:
        raise HTTPException(429, "This report has reached its five-attempt limit")
    result = await session.execute(update(AIReport).where(
        AIReport.id == report_id, AIReport.generation_attempt == report.generation_attempt,
        AIReport.attempt_count < MAX_ATTEMPTS,
        or_(AIReport.status != "pending", AIReport.last_attempt_at < now - STALE_AFTER),
    ).values(status="pending", language=language, error_code=None, updated_at=now, last_attempt_at=now,
             attempt_count=AIReport.attempt_count + 1, generation_attempt=AIReport.generation_attempt + 1)
        .returning(AIReport).execution_options(populate_existing=True))
    claimed = result.scalar_one_or_none()
    if claimed is None:
        await session.rollback()
        raise HTTPException(409, "Report generation is already in progress")
    await consume_budget(session, settings, host, claimed.token_hash)
    await session.commit()
    return await generate(session, claimed, module, settings)


async def history(session: AsyncSession, user_id: UUID, settings: Settings) -> dict:
    rows = (await session.execute(select(
        AIReport.id, AIReport.service_type, AIReport.status, AIReport.created_at
    ).where(AIReport.user_id == user_id, AIReport.created_at >= retention_cutoff(settings))
        .order_by(AIReport.created_at.desc()).limit(100))).all()
    return {"reports": [{"id": str(row.id), "service_type": row.service_type,
                         "status": row.status, "created_at": row.created_at.isoformat()} for row in rows]}


def member_output(member: AIReportFamilyMember) -> dict:
    return {"id": str(member.id), "label": member.label, "details": member.details,
            "created_at": member.created_at.isoformat()}


async def family_members(session: AsyncSession, user_id: UUID) -> dict:
    members = (await session.scalars(select(AIReportFamilyMember).where(
        AIReportFamilyMember.user_id == user_id
    ).order_by(AIReportFamilyMember.created_at.desc()).limit(100))).all()
    return {"members": [member_output(member) for member in members]}


async def save_member(session: AsyncSession, user_id: UUID, payload, settings: Settings, member_id: UUID | None = None) -> dict:
    details = payload.details.model_dump(mode="json")
    if member_id is None:
        await advisory_lock(session, f"ai-report-family:{user_id}")
        count = await session.scalar(select(func.count()).select_from(AIReportFamilyMember).where(
            AIReportFamilyMember.user_id == user_id
        ))
        limit = min(20, max(0, getattr(settings, "ai_report_family_limit", 20)))
        if count >= limit:
            raise HTTPException(409, "Your family member limit has been reached")
        member = AIReportFamilyMember(user_id=user_id, label=payload.label, details=details)
        session.add(member)
        await session.flush()
    else:
        result = await session.execute(update(AIReportFamilyMember).where(
            AIReportFamilyMember.id == member_id, AIReportFamilyMember.user_id == user_id
        ).values(label=payload.label, details=details, updated_at=now_utc()).returning(AIReportFamilyMember))
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(404, "Family member not found")
    output = {"member": member_output(member)}
    await session.commit()
    return output


async def delete_member(session: AsyncSession, user_id: UUID, member_id: UUID) -> None:
    result = await session.execute(delete(AIReportFamilyMember).where(
        AIReportFamilyMember.id == member_id, AIReportFamilyMember.user_id == user_id
    ).returning(AIReportFamilyMember.id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(404, "Family member not found")
    await session.commit()