"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers.developer import urbanroute
from .config import get_settings


app = FastAPI(
    title="Developer API",
    description="Provides routes not yet exposed to the public and tools for developers",
    version="0.0.1",
    root_path=get_settings().root_path,
)


app.include_router(urbanroute.router, tags=["Developer"])
