from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from cleanair.databases.tables import JamCamVideoStats
from ..databases import get_db
from ..databases import schemas

router = APIRouter()


@router.get("/recent", response_model=List[schemas.JamCamVideo])
async def cam_recent(
    id: str, db: Session = Depends(get_db),
):

    return (
        db.query(JamCamVideoStats)
        .filter(JamCamVideoStats.camera_id == (id + ".mp4"))
        .all()
    )


@router.get("/snapshot")
async def cam_snapshot(id: str):
    return
