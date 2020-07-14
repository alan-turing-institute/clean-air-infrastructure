"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import jamcam, static, forecast_historic
from .config import get_settings


app = FastAPI(
    title="UrbanAir API",
    description="High resolution air polution forecasts",
    version="0.0.1",
)


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
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
app.include_router(
    forecast_historic.router, prefix="/api/v1/forecasts", tags=["forecasts"]
)
