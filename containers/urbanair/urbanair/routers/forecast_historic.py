from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, Response, HTTPException

from ..databases.schemas.forecast_historic import ForecastAvailable
from ..databases.queries.forecast_historic import get_forecast_available
from ..databases import get_db, all_or_404

router = APIRouter()


@router.get("/forecast_info", description="GeoJSON: Forecast point data.")
async def forecast_info(
    instance_id: str = Query(
        "instance_id", description="This is a historic forecast route"
    )
) -> Dict:

    return {"data": "A sample route"}


@router.get(
    "/forecast_available",
    description=" Forecast info",
    response_model=List[ForecastAvailable],
)
async def forecast_available(db: Session = Depends(get_db)) -> Optional[List[Dict]]:

    data = get_forecast_available(db)

    return all_or_404(data)
