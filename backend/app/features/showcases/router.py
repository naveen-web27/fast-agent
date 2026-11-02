"""Linked-video discovery and provider-owned publishing."""
from collections.abc import Awaitable
from typing import TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.features.profiles.service import ProfileAccessError, ProfileNotFoundError
from app.features.showcases.links import parse_video_link
from app.features.showcases.schemas import (
    ManagedShowcases, PreviewInput, ShowcaseInput, ShowcaseList, ShowcaseOut, VideoPreview,
)
from app.features.showcases.service import (
    ShowcaseConflictError, list_showcases, managed_showcases, remove_showcase, save_showcase,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()
T = TypeVar("T")


async def _run(action: Awaitable[T]) -> T:
    try:
        return await action
    except ProfileNotFoundError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except ProfileAccessError as exc:
        raise HTTPException(403, detail=str(exc)) from exc
    except ShowcaseConflictError as exc:
        raise HTTPException(409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc


@router.get("/showcases", response_model=ShowcaseList)
async def browse_showcases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=30),
    profile_id: UUID | None = None,
    session: AsyncSession = Depends(get_db),
) -> ShowcaseList:
    return await list_showcases(session, page, page_size, profile_id)


@router.post("/showcases/preview", response_model=VideoPreview)
async def preview_video(payload: PreviewInput, _: UUID = Depends(get_current_auth_user_id)) -> VideoPreview:
    try:
        video = parse_video_link(payload.source_url)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc)) from exc
    return VideoPreview(
        source_url=video.url, platform=video.platform, thumbnail_url=video.thumbnail_url,
        message=(
            "Check the YouTube thumbnail below. If unavailable, upload your own cover."
            if video.thumbnail_url else
            "Instagram previews are not fetched. Upload your own thumbnail or poster to continue."
        ),
    )


@router.get("/profiles/{profile_id}/showcases/manage", response_model=ManagedShowcases)
async def get_managed_showcases(
    profile_id: UUID, auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> ManagedShowcases:
    return await _run(managed_showcases(session, auth_user_id, profile_id))


@router.post("/profiles/{profile_id}/showcases", response_model=ShowcaseOut, status_code=201)
async def create_showcase(
    profile_id: UUID, payload: ShowcaseInput,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings),
) -> ShowcaseOut:
    return await _run(save_showcase(session, auth_user_id, profile_id, payload, settings.supabase_url))


@router.put("/profiles/{profile_id}/showcases/{showcase_id}", response_model=ShowcaseOut)
async def edit_showcase(
    profile_id: UUID, showcase_id: UUID, payload: ShowcaseInput,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db), settings: Settings = Depends(get_settings),
) -> ShowcaseOut:
    return await _run(save_showcase(session, auth_user_id, profile_id, payload, settings.supabase_url, showcase_id))


@router.delete("/profiles/{profile_id}/showcases/{showcase_id}", status_code=204)
async def delete_showcase(
    profile_id: UUID, showcase_id: UUID, auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> None:
    await _run(remove_showcase(session, auth_user_id, profile_id, showcase_id))
