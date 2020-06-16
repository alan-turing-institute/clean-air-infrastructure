from fastapi import APIRouter
from datetime import datetime, time

router = APIRouter()


@router.get("hourly/raw")
async def hourly_raw(starttime: datetime, endtime: datetime):
    return "Not implimented"


@router.get("daily/raw")
async def daily_raw(starttime: datetime, endtime: datetime):
    return "Not implimented"


@router.get("hourly/raw/availability")
async def availability_hourly_raw(
    starttime: datetime, endtime: datetime, only_missing: bool
):
    return "Not implimented"
