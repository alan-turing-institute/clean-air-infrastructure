"""UrbanAir API"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import jamcam, static
from .config import get_settings


app = FastAPI(
    title="Odysseus API",
    description="API for trusted partners",
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
app.include_router(jamcam.router, prefix="/api/v1/jamcams", tags=["jamcam"])
