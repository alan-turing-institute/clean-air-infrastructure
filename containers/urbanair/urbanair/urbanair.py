"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers.urbanair import static
from .config import get_settings


app = FastAPI(
    title="UrbanAir API",
    description="High resolution air pollution forecasts",
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
