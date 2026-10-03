"""RightConnect FastAPI application entry point."""
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.features.router import feature_router

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(feature_router, prefix=settings.api_prefix)

admin_page = Path(__file__).resolve().parents[1] / "admin" / "index.html"
admin_basic = HTTPBasic(realm="RightConnect admin")


def _require_admin_basic(credentials: HTTPBasicCredentials = Depends(admin_basic)) -> None:
    user_ok = secrets.compare_digest(credentials.username.encode(), settings.admin_basic_user.encode())
    password_ok = secrets.compare_digest(credentials.password.encode(), settings.admin_basic_password.encode())
    if not (user_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="RightConnect admin"'},
        )


# Admin UI is off unless ADMIN_PATH and both Basic-auth credentials are configured.
if settings.admin_path.startswith("/") and len(settings.admin_path) > 1 and settings.admin_basic_user and settings.admin_basic_password:

    @app.get(settings.admin_path.rstrip("/"), include_in_schema=False, dependencies=[Depends(_require_admin_basic)])
    async def admin_console() -> FileResponse:
        return FileResponse(admin_page, headers={"Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow"})


@app.get("/.well-known/assetlinks.json", include_in_schema=False)
async def android_asset_links() -> list[dict]:
    fingerprints = [fp.strip().upper() for fp in settings.android_sha256_fingerprints.split(",") if fp.strip()]
    if not fingerprints:
        return []
    return [
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": settings.android_package_name,
                "sha256_cert_fingerprints": fingerprints,
            },
        }
    ]


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")