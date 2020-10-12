"""UrbanAir API"""
import os
import logging
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from .routers.urbanair import static, air_quality_forecast
from .config import get_settings
from .security import get_http_username

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

app = FastAPI(
    title="UrbanAir API",
    description="High resolution air pollution forecasts",
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

# Mount documentation
if get_settings().mount_docs:

    app.mount(
        "/welcome",
        StaticFiles(
            directory=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "docs", "urbanair"
            ),
            html=True,
        ),
        name="welcome",
    )
    logger.info("Mount API documentation")

app.include_router(static.router,)
app.include_router(
    air_quality_forecast.router,
    prefix="/api/v1/air_quality",
    tags=["airquality"],
    dependencies=[Depends(get_http_username)],
)
