"""Single registry for all feature routers imported by the application entry point."""
from fastapi import APIRouter

from app.features.auth.router import router as auth_router
from app.features.health.router import router as health_router

feature_router = APIRouter()
feature_router.include_router(health_router, tags=["health"])
feature_router.include_router(auth_router, prefix="/auth", tags=["auth"])