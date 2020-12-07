"""UrbanAir API"""
import os
import logging
from typing import Union
from fastapi import FastAPI, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from starlette.middleware.sessions import SessionMiddleware
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from .routers.odysseus import static, jamcam
from .routers.auth import auth
from .config import get_settings, AuthSettings
from .security import (
    get_http_username,
    oauth_basic_user,
    oauth_admin_user,
    oauth_enhanced_user,
    RequiresLoginException,
    logged_in,
)

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

app = FastAPI(
    title="Odysseus API",
    description="Project Odysseus API",
    version="0.0.1",
    root_path=get_settings().root_path,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
sentry_dsn = get_settings().sentry_dsn  # pylint: disable=C0103
if sentry_dsn:
    sentry_sdk.init(dsn=get_settings().sentry_dsn)
    app.add_middleware(SentryAsgiMiddleware)
    logger.info("Adding sentry logging middleware")
else:
    logging.warning("Sentry is not logging errors")

auth_settings = AuthSettings()
app.add_middleware(
    SessionMiddleware,
    secret_key=auth_settings.session_secret.get_secret_value(),
    max_age=24 * 60 * 60,
)

app.mount(
    f"{app.root_path}/static",
    StaticFiles(
        directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    ),
    name="static",
)


@app.exception_handler(RequiresLoginException)
async def exception_handler(request: Request, exc: RequiresLoginException) -> Response:
    "An exception with redirects to login"
    return RedirectResponse(url=request.url_for("home"))


# Static routes require login session
app.include_router(static.router)

# Add routes for logging in and generating access token
app.include_router(auth.router, tags=["auth"])

# Other routes protected by oauth
app.include_router(
    jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"],
)


@app.get("/openapi.json", include_in_schema=False)
async def get_open_api_endpoint(
    _=Depends(logged_in),
) -> Union[JSONResponse, HTMLResponse]:
    return JSONResponse(
        get_openapi(title="Odysseus API", version="0.0.1", routes=app.routes)
    )


@app.get("/docs", include_in_schema=False)
async def get_documentation(_=Depends(logged_in)) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/openapi.json", title="docs")


@app.get("/redoc", include_in_schema=False)
async def get_redocumentation(_=Depends(logged_in)) -> HTMLResponse:
    return get_redoc_html(openapi_url="/openapi.json", title="docs")

