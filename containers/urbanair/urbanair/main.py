"""UrbanAir API"""
import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from .routers import air_quality_forecast, jamcam, static
from .config import get_settings

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

app = FastAPI(
    title="UrbanAir API",
    description="High resolution air pollution forecasts",
    version="0.0.1",
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

if not get_settings().docker:
    app.mount(
        "/package/docs",
        StaticFiles(
            directory=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "packages"
            ),
            html=True,
        ),
        name="package_docs",
    )

app.include_router(static.router)
app.include_router(
    air_quality_forecast.router, prefix="/api/v1/air_quality", tags=["airquality"]
)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
