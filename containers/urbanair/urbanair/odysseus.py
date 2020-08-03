"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers.odysseus import static, jamcam
from .config import get_settings


app = FastAPI(
    title="Odysseus API", description="Project Odysseus API", version="0.0.1",
)

app.include_router(static.router)
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
