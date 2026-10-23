"""Server-side Thirumana porutham: free Rasi check, Kattam preview and paid full report."""
from functools import partial

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import Settings, get_settings
from app.features.payments.router import razorpay_api

from . import report, service
from .contracts import KattamRequest, RasiRequest, UnlockRequest

router = APIRouter()


def run(call):
    try:
        return call()
    except service.ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/rasi")
def rasi_porutham(body: RasiRequest) -> dict:
    data = body.model_dump()
    return report.rasi_report(data["bride"], data["groom"], body.language)


@router.post("/kattam")
def kattam_preview(body: KattamRequest, settings: Settings = Depends(get_settings)) -> dict:
    full = run(lambda: service.build(body.model_dump(mode="json")))
    return {"report": report.preview(full, body.language), "unlock": service.unlock_offer(settings)}


@router.post("/kattam/order")
async def kattam_order(body: KattamRequest, settings: Settings = Depends(get_settings)) -> dict:
    try:
        return await service.create_order(body.model_dump(mode="json"), settings, partial(razorpay_api, settings))
    except service.ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/kattam/full")
async def kattam_full(body: UnlockRequest, settings: Settings = Depends(get_settings)) -> dict:
    try:
        return await service.unlock(body.model_dump(mode="json"), settings, partial(razorpay_api, settings))
    except service.ServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
