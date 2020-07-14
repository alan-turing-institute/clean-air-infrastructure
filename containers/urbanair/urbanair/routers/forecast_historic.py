from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Response, HTTPException

from ..databases.schemas.forecast_historic import (
    ForecastAvailable
)
from ..databases.queries.forecast_historic import (
    get_forecast_available
   
)

router = APIRouter()


@router.get("/forecast_info", description="GeoJSON: Forecast point data.")
async def forecast_info(
    instance_id: str = Query(
        "instance_id", description="This is a historic forecast route"
    )
) -> Dict:

    return {"data": "A sample route"}


@router.get("/forecast_available", description=" Forecast info")
async def forecast_available() -> Response:
    return get_forecast_available() 