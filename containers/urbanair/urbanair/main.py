"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import jamcam, static
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

if get_settings().is_docker:
    app.mount(
        "/package/docs",
        StaticFiles(
            directory=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "packages"
            ),
            html=True,
        ),
        name="packages",
    )

app.include_router(static.router)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
