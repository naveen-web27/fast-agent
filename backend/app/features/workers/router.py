"""HTTP endpoints for the local workforce hub (workers / service partners)."""
from collections.abc import Awaitable
from typing import Literal, TypeVar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.features.workers import service
from app.features.workers.schemas import (
    AvailabilityUpdate,
    ClaimWorkerPayload,
    CompanyOption,
    EmployerExperienceCreate,
    ExperienceConfirm,
    ExperienceCreate,
    HireCreate,
    HireOut,
    HiresResponse,
    JobApply,
    JobCreate,
    JobOut,
    MyWorkerProfile,
    ReviewCreate,
    VerificationRequestOut,
    WorkerCreate,
    WorkerDetail,
    WorkerListResponse,
    WorkerUpdate,
)
from app.security.dependencies import get_current_auth_user_id

router = APIRouter()

T = TypeVar("T")
ERROR_STATUS = {
    service.WorkerNotFoundError: status.HTTP_404_NOT_FOUND,
    service.WorkerIdentityError: status.HTTP_404_NOT_FOUND,
    service.WorkerAccessError: status.HTTP_403_FORBIDDEN,
    service.WorkerConflictError: status.HTTP_409_CONFLICT,
}


async def run_worker_action(action: Awaitable[T]) -> T:
    try:
        return await action
    except tuple(ERROR_STATUS) as exc:
        raise HTTPException(status_code=ERROR_STATUS[type(exc)], detail=str(exc)) from exc


# Fixed paths come before /{worker_id} so "me", "jobs" and "hires" aren't parsed as IDs.


@router.get("", response_model=WorkerListResponse)
async def search(
    q: str | None = Query(default=None, max_length=200),
    city: str | None = Query(default=None, max_length=100),
    area: str | None = Query(default=None, max_length=100),
    available: bool = Query(default=False, description="Only workers who are free now"),
    near: str | None = Query(default=None, pattern=r"^[1-9][0-9]{5}$", description="Searcher's PIN code: nearest first"),
    near_city: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
) -> WorkerListResponse:
    """Find workers: nearest first (when the searcher's location is known), then available ones."""
    return await service.search_workers(session, q, city, area, available, page, page_size, near, near_city)


@router.get("/me", response_model=MyWorkerProfile)
async def my_profile(
    auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    profile = await run_worker_action(service.get_my_worker(session, auth_user_id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You don't have a worker profile yet")
    return profile


@router.post("/me", response_model=MyWorkerProfile, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: WorkerCreate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    return await run_worker_action(service.create_my_worker(session, auth_user_id, payload))


@router.put("/me", response_model=MyWorkerProfile)
async def update_profile(
    payload: WorkerUpdate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    return await run_worker_action(service.update_my_worker(session, auth_user_id, payload))


@router.put("/me/availability", response_model=MyWorkerProfile)
async def update_availability(
    payload: AvailabilityUpdate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    """Green = available, amber = busy (optionally until a date), grey = offline."""
    return await run_worker_action(service.set_my_availability(session, auth_user_id, payload))


@router.post("/me/experiences", response_model=MyWorkerProfile, status_code=status.HTTP_201_CREATED)
async def add_experience(
    payload: ExperienceCreate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    """Add a past job. Picking a company on RightConnect asks that company to confirm it."""
    return await run_worker_action(service.add_my_experience(session, auth_user_id, payload))


@router.delete("/me/experiences/{experience_id}", response_model=MyWorkerProfile)
async def remove_experience(
    experience_id: UUID, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    return await run_worker_action(service.delete_my_experience(session, auth_user_id, experience_id))


@router.post("/claim", response_model=MyWorkerProfile)
async def claim(
    payload: ClaimWorkerPayload, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> MyWorkerProfile:
    """Take over a profile RightConnect created for you, using the code you were given."""
    return await run_worker_action(service.claim_worker_profile(session, auth_user_id, payload.code))


@router.get("/companies", response_model=list[CompanyOption])
async def companies(q: str = Query(min_length=2, max_length=120), session: AsyncSession = Depends(get_db)) -> list[CompanyOption]:
    """Type-ahead for picking a past employer that is on RightConnect."""
    return [CompanyOption(**row) for row in await service.search_companies(session, q)]


@router.get("/verifications", response_model=list[VerificationRequestOut])
async def verification_requests(
    auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> list[VerificationRequestOut]:
    """Work history that workers asked your company to confirm."""
    return await run_worker_action(service.list_verification_requests(session, auth_user_id))


@router.post("/verifications/{experience_id}/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def confirm(
    experience_id: UUID,
    payload: ExperienceConfirm,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> None:
    await run_worker_action(service.confirm_experience(session, auth_user_id, experience_id, payload))


@router.post("/verifications/{experience_id}/decline", status_code=status.HTTP_204_NO_CONTENT)
async def decline(
    experience_id: UUID, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> None:
    await run_worker_action(service.decline_experience(session, auth_user_id, experience_id))


@router.get("/hires", response_model=HiresResponse)
async def hires(auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)) -> HiresResponse:
    return await run_worker_action(service.list_hires(session, auth_user_id))


@router.post("/hires/{hire_id}/review", response_model=HireOut, status_code=status.HTTP_201_CREATED)
async def review(
    hire_id: UUID, payload: ReviewCreate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> HireOut:
    return await run_worker_action(service.review_hire(session, auth_user_id, hire_id, payload))


@router.post("/hires/{hire_id}/{action}", response_model=HireOut)
async def change_hire(
    hire_id: UUID,
    action: Literal["accept", "decline", "cancel", "complete"],
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> HireOut:
    return await run_worker_action(service.hire_action(session, auth_user_id, hire_id, action))


@router.get("/jobs", response_model=list[JobOut])
async def jobs(
    q: str | None = Query(default=None, max_length=200),
    city: str | None = Query(default=None, max_length=100),
    near: str | None = Query(default=None, pattern=r"^[1-9][0-9]{5}$"),
    near_city: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    session: AsyncSession = Depends(get_db),
) -> list[JobOut]:
    return await service.list_open_jobs(session, q, city, page, page_size, near, near_city)


@router.get("/jobs/mine", response_model=list[JobOut])
async def my_jobs(auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)) -> list[JobOut]:
    return await run_worker_action(service.list_my_jobs(session, auth_user_id))


@router.post("/jobs", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def post_job(
    payload: JobCreate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> JobOut:
    return await run_worker_action(service.create_job(session, auth_user_id, payload))


@router.post("/jobs/{job_id}/close", response_model=JobOut)
async def close(job_id: UUID, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)) -> JobOut:
    return await run_worker_action(service.close_job(session, auth_user_id, job_id))


@router.post("/jobs/{job_id}/apply", response_model=HireOut, status_code=status.HTTP_201_CREATED)
async def apply(
    job_id: UUID, payload: JobApply, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> HireOut:
    return await run_worker_action(service.apply_to_job(session, auth_user_id, job_id, payload))


@router.get("/{worker_id}", response_model=WorkerDetail)
async def worker_detail(worker_id: UUID, session: AsyncSession = Depends(get_db)) -> WorkerDetail:
    return await run_worker_action(service.get_worker(session, worker_id))


@router.post("/{worker_id}/hire", response_model=HireOut, status_code=status.HTTP_201_CREATED)
async def hire(
    worker_id: UUID, payload: HireCreate, auth_user_id: UUID = Depends(get_current_auth_user_id), session: AsyncSession = Depends(get_db)
) -> HireOut:
    return await run_worker_action(service.create_hire(session, auth_user_id, worker_id, payload))


@router.post("/{worker_id}/experiences", status_code=status.HTTP_201_CREATED)
async def employer_experience(
    worker_id: UUID,
    payload: EmployerExperienceCreate,
    auth_user_id: UUID = Depends(get_current_auth_user_id),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """A company admin certifies work this person did for them; the listed skills become employer-verified."""
    await run_worker_action(service.employer_add_experience(session, auth_user_id, worker_id, payload))
    return {"status": "added"}
