"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import jamcam, static
from .config import get_settings


app = FastAPI(
    title="Developer API",
    description="Provides routes not yet exposed to the public and tools for developers",
    version="0.0.1",
)

app.include_router(static.router)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
