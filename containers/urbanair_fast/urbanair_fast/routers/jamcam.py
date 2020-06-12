from fastapi import APIRouter

router = APIRouter()


@router.get("/recent")
async def cam_recent(id: str):
    return


@router.get("/snapshot")
async def cam_snapshot(id: str):
    return
