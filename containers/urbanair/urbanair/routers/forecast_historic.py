from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query, Response, HTTPException

from ..databases.schemas.forecast_historic import ForecastBase
from ..databases.queries.forecast_historic import get_forecast_values,get_forecast_available
from ..databases import get_db, all_or_404

ONE_WEEK_SECONDS = 7 * 24 * 60 * 60
ONE_DAYS_SECONDS = 1 * 24 * 60 * 60
router = APIRouter()

async def common_forecast_params(
    starttime: datetime = Query(
        None, description="""ISO UTC datetime to request data from""",
    ),
    endtime: datetime = Query(
        None,
        description="ISO UTC datetime to request data up to (not including this datetime)",
    ),
) -> Dict:
    
    return {
        "starttime": starttime,
        "endtime": endtime,
    }

@router.get("/forecast_example", description="Forecast example route")
async def forecast_example(
    instance_id: str = Query(
        "instance_id", description="This is a historic forecast route"
    )
) -> Dict:

    return {"data": "A sample route"}


@router.get(
    "/forecast_info",
    description="JSON: Forecast data values",
    response_model=List[ForecastBase],
)
async def forecast_info(db: Session = Depends(get_db)) -> Optional[List[Dict]]:

    data = get_forecast_values(db)

    return all_or_404(data)


@router.get(
    "/forecast_available",
    description="""Check what forecast data is available between starttime and endtime.
    If starttime and endtime are not provided checks all availability""",
    response_model=List[ForecastBase],
)
async def forecast_available(
    commons: dict = Depends(common_forecast_params),
    db: Session = Depends(get_db)
    ) -> Optional[List[Dict]]:

    data = get_forecast_available(db,
        commons["starttime"],
        commons["endtime"],)

    return all_or_404(data)


