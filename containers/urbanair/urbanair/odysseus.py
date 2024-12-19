"""UrbanAir API"""

import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from .routers.odysseus import static, jamcam
from .config import get_settings

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

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
    f"{app.root_path}/static",
    StaticFiles(
        directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    ),
    name="static",
)

app.include_router(static.router)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
