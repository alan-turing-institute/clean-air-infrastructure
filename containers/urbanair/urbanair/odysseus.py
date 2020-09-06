"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers.odysseus import static, jamcam
from .config import get_settings


app = FastAPI(
    title="Odysseus API",
    description="Project Odysseus API",
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
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
