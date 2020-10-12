"""UrbanAir API"""
import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers.developer import urbanroute
from .config import get_settings

logger = logging.getLogger("fastapi")  # pylint: disable=invalid-name

app = FastAPI(
    title="Developer API",
    description="Provides routes not yet exposed to the public and tools for developers",
    version="0.0.1",
    root_path=get_settings().root_path,
)

# Mount documentation
if get_settings().mount_docs:

    app.mount(
        "/package/docs",
        StaticFiles(
            directory=os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "docs", "dev"
            ),
            html=True,
        ),
        name="packages",
    )
    logger.info("Mount dev documentation")

app.include_router(urbanroute.router, tags=["Developer"])
