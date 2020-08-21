"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import air_quality_forecast, jamcam, static
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
app.include_router(
    air_quality_forecast.router, prefix="/api/v1/air_quality", tags=["airquality"]
)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
