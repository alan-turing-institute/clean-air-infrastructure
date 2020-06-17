from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.orm import Session
from .config import get_settings, Settings
from .routers import jamcam, static
from .databases import get_db

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
