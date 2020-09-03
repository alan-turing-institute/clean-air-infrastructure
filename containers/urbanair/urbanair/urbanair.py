"""UrbanAir API"""
import os
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

# from .routers.urbanair import static
from .routers.urbanair import static, air_quality_forecast
from .config import get_settings

app = FastAPI(
    title="UrbanAir API",
    description="High resolution air pollution forecasts",
    version="0.0.1",
    root_path=get_settings().root_path,
)

app.mount(
    "/static",
    StaticFiles(
        directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    ),
    name="static",
)

app.include_router(static.router)
app.include_router(
    air_quality_forecast.router, prefix="/api/v1/air_quality", tags=["airquality"]
)
