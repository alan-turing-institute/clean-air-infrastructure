from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.orm import Session
from .config import get_settings, Settings
from .routers import jamcam, scoot
from .databases import get_db
from cleanair.databases.tables import StreetCanyon


from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


PARENT_DIR_PATH = os.path.dirname(os.path.abspath(__file__))

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

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
)


@app.get("/")
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/items/{id}")
async def read_item(request: Request, id: str):
    return templates.TemplateResponse("item.html", {"request": request, "id": id})


@app.get("/map")
async def read_item(request: Request):
    return templates.TemplateResponse("map.html", {"request": request})


app.include_router(jamcam.router, prefix="/jamcam", tags=["jamcam"])
app.include_router(scoot.router, prefix="/scoot", tags=["scoot"])


@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "secrets": settings.database_secret_file,
    }
