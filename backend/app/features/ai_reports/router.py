"""Private, capability-addressed reports with optional verified account ownership."""
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import active_user_by_auth_id
from app.security.dependencies import bearer_scheme, get_current_auth_user_id

from . import service
from .contracts import BirthInput, ReportRequest, StrictInput


class BoundedReportRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def bounded_handler(request: Request) -> Response:
            if request.method in {"POST", "PUT"}:
                body = bytearray()
                async for chunk in request.stream():
                    if len(body) + len(chunk) > 16384:
                        raise HTTPException(413, "Report request exceeds 16 KB")
                    body.extend(chunk)
                request._body = bytes(body)
            try:
                response = await handler(request)
            except RequestValidationError:
                raise HTTPException(422, "Invalid request; check the required fields and values") from None
            response.headers["Cache-Control"] = "no-store"
            return response

        return bounded_handler


router = APIRouter(prefix="/ai-reports", tags=["ai-reports"], route_class=BoundedReportRoute)


class LanguageRequest(StrictInput):
    language: Literal["ta", "en"]


class FamilyPayload(StrictInput):
    label: str = Field(min_length=1, max_length=80)
    details: BirthInput
    consent: Literal[True]


async def optional_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db),
) -> UUID | None:
    if "authorization" not in request.headers:
        return None
    if credentials is None:
        raise HTTPException(401, "A valid Bearer authorization header is required")
    auth_id = await get_current_auth_user_id(credentials=credentials, settings=settings, session=session)
    user = await session.scalar(active_user_by_auth_id(auth_id))
    if user is None:
        raise HTTPException(403, "Complete account onboarding before using AI reports while signed in")
    if user.blocked_at is not None:
        raise HTTPException(403, "Your account is suspended")
    return user.id


async def required_user_id(user_id: UUID | None = Depends(optional_user_id)) -> UUID:
    if user_id is None:
        raise HTTPException(401, "Sign in to access your report history and family members")
    return user_id


def client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.get("/services")
async def services(settings: Settings = Depends(get_settings)) -> dict:
    return service.catalogue(settings)


@router.get("/history/me")
async def history(
    user_id: UUID = Depends(required_user_id), session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return await service.history(session, user_id, settings)


@router.get("/family/members")
async def family_members(
    user_id: UUID = Depends(required_user_id), session: AsyncSession = Depends(get_db),
) -> dict:
    return await service.family_members(session, user_id)


@router.post("/family/members", status_code=201)
async def create_family_member(
    payload: FamilyPayload, user_id: UUID = Depends(required_user_id),
    session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings),
) -> dict:
    return await service.save_member(session, user_id, payload, settings)


@router.put("/family/members/{member_id}")
async def update_family_member(
    member_id: UUID, payload: FamilyPayload, user_id: UUID = Depends(required_user_id),
    session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings),
) -> dict:
    return await service.save_member(session, user_id, payload, settings, member_id)


@router.delete("/family/members/{member_id}", status_code=204)
async def delete_family_member(
    member_id: UUID, user_id: UUID = Depends(required_user_id), session: AsyncSession = Depends(get_db),
) -> Response:
    await service.delete_member(session, user_id, member_id)
    return Response(status_code=204)


@router.get("/{report_id}")
async def get_report(
    report_id: UUID, token: str | None = Header(default=None, alias="X-Report-Token"),
    user_id: UUID | None = Depends(optional_user_id), session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return service.report_output(await service.authorized_report(session, report_id, user_id, token, settings))


@router.post("/{report_id}/retry")
async def retry_report(
    report_id: UUID, payload: LanguageRequest, request: Request,
    token: str | None = Header(default=None, alias="X-Report-Token"),
    user_id: UUID | None = Depends(optional_user_id), session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return await service.change_report(session, report_id, payload.language, user_id, token, client_host(request), settings)


@router.post("/{report_id}/language")
async def change_language(
    report_id: UUID, payload: LanguageRequest, request: Request,
    token: str | None = Header(default=None, alias="X-Report-Token"),
    user_id: UUID | None = Depends(optional_user_id), session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return await service.change_report(
        session, report_id, payload.language, user_id, token, client_host(request), settings, translation=True
    )


@router.post("/{service_type}")
async def create_report(
    service_type: str, payload: ReportRequest, request: Request,
    token: str = Header(alias="X-Report-Token"),
    user_id: UUID | None = Depends(optional_user_id), session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    return await service.create_report(session, service_type, payload, token, user_id, client_host(request), settings)