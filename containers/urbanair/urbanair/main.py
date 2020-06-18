"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import jamcam, static


# pylint
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


app.include_router(static.router)
app.include_router(jamcam.router, prefix="/api/v1/cams", tags=["jamcam"])
