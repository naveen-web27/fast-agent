"""Single registry for all feature routers imported by the application entry point."""
from fastapi import APIRouter

from app.features.admin.router import router as admin_router
from app.features.auth.router import router as auth_router
from app.features.booking.router import router as booking_router
from app.features.dashboard.router import router as dashboard_router
from app.features.health.router import router as health_router
from app.features.marketplace.router import router as marketplace_router
from app.features.organizations.router import router as organizations_router
from app.features.payments.router import router as payments_router
from app.features.profiles.router import router as profiles_router
from app.features.requests.router import router as requests_router

feature_router = APIRouter()
feature_router.include_router(health_router, tags=["health"])
feature_router.include_router(auth_router, prefix="/auth", tags=["auth"])
feature_router.include_router(marketplace_router, tags=["marketplace"])
feature_router.include_router(profiles_router, tags=["profiles"])
feature_router.include_router(admin_router, prefix="/admin", tags=["admin"])
feature_router.include_router(requests_router, prefix="/requests", tags=["requests"])
feature_router.include_router(booking_router, prefix="/requests", tags=["booking"])
feature_router.include_router(organizations_router, prefix="/organizations", tags=["organizations"])
feature_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
feature_router.include_router(payments_router, prefix="/payments", tags=["payments"])
