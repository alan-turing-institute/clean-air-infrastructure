from fastapi import Depends, FastAPI, Header, HTTPException
from sqlalchemy.orm import Session
from .config import get_settings, Settings
from .routers import jamcam, scoot
from .databases import get_db

from cleanair.databases.tables import StreetCanyon

app = FastAPI(
    title="UrbanAir API",
    description="High resolution air polution forecasts",
    version="0.0.1",
)


app.include_router(jamcam.router, prefix="/jamcam", tags=["jamcam"])
app.include_router(scoot.router, prefix="/scoot", tags=["scoot"])


@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {
        "app_name": settings.app_name,
        "admin_email": settings.admin_email,
        "secrets": settings.database_secret_file,
    }


@app.get("/testdb")
async def info(db: Session = Depends(get_db)):

    print(db.query(StreetCanyon).limit(10).all())
    return "hi"
