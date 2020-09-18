"""UrbanAir API"""
import os
import logging
from fastapi import FastAPI, Request, Depends, Response, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from passlib.apache import HtpasswdFile
from .routers.odysseus import static, jamcam
from .config import get_settings

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

security = HTTPBasic()

app = FastAPI(
    title="Odysseus API",
    description="Project Odysseus API",
    version="0.0.1",
    root_path=get_settings().root_path,
)

sentry_dsn = get_settings().sentry_dsn  # pylint: disable=C0103
if sentry_dsn:
    sentry_sdk.init(dsn=get_settings().sentry_dsn)
    app.add_middleware(SentryAsgiMiddleware)
    logger.info("Adding sentry logging middleware")
else:
    logging.warning("Sentry is not logging errors")

app.mount(
    "/static",
    StaticFiles(
        directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    ),
    name="static",
)

app.include_router(static.router)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    ht = HtpasswdFile("test.htpasswd")
    correct_username_and_password = ht.check_password(credentials.username, credentials.password)

    if not (correct_username_and_password):
        raise HTTPException(
            401,
            detail = "Incorrect username or password",
            headers = {"WWW-Authenticate": "Basic"},
            )
    return credentials.username

@app.middleware("http")
async def authenticate(request: Request, call_next, username: str = Depends(get_current_username),) -> Response:
    logging.info("Calling authentication middleware")
    return await call_next(request)
