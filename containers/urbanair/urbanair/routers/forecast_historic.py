"""Forecast API routes"""
# pylint: disable=C0116
from collections.abc import Iterable
from typing import List, Dict, Optional
from datetime import date
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query
from cleanair.types import Source
from ..databases.schemas.forecast_historic import (
    ForecastBase,
    ForecastResultBase,
    AirPollutionFeature,
    AirPollutionFeatureCollection,
)
from ..databases.queries.forecast_historic import (
    get_forecast_available,
    get_forecast,
    get_forecast_json,
)
from ..databases import get_db, all_or_404


router = APIRouter()


async def common_forecast_id(
    instance_id: str = Query(None, description="A unique forecast instance id")
) -> Dict:
    """Common ids in forecast routes."""
    return {"instance_id": instance_id}


@router.get(
    "/available",
    description="""Check what forecast data is available between starttime and endtime.
    If starttime and endtime are not provided checks all availability""",
    response_model=List[ForecastBase],
)
async def forecast_available(
    startdate: date = Query(None, description="""ISO UTC date to request data from""",),
    enddate: date = Query(
        None,
        description="ISO UTC date to request data up to (not including this date)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_forecast_available(db, startdate, enddate)
    return all_or_404(data)


@router.get(
    "/forecast",
    description="A single forecast",
    response_model=List[ForecastResultBase],
)
async def forecast(
    instance_id: str = Query(None, description="A unique forecast instance id"),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_forecast(db, instance_id)
    return all_or_404(data)


@router.get(
    "/forecast_geojson",
    description="Geojson: Forecast models result values filter by instance_id",
    response_model=AirPollutionFeatureCollection,
)
async def forecast_geojson(
    instance_id: str = Query(None, description="A unique forecast instance id"),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    data = get_forecast_json(db, instance_id)

    out = all_or_404(data)

    if out:
        return {"features": [i[0] for i in out]}
