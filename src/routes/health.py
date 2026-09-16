"""Uptime check endpoint (Render free tier sleeps on inactivity; pings keep it warm)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok"}
