"""Air quality forecast API routes"""
from collections.abc import Iterable
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query
from cleanair.types import Source
from ..databases import get_db, all_or_404
from ..databases.schemas.air_quality_forecast import (
    ForecastResultGeoJson, GeoJsonPointFeature,
    ForecastResultJson,
)
from ..databases.queries.air_quality_forecast import (
    get_available_instance_ids,
    get_forecasts,
    get_forecasts_with_location,
)


router = APIRouter()


@router.get(
    "/forecast_json",
    description="Most up-to-date forecasts for a given day in JSON",
    response_model=List[ForecastResultJson],
)
async def forecast_json(
    date: date = Query(None, description="Date to retrieve forecasts for"),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:

    # Establish start and end datetimes
    start_datetime = datetime.combine(date, datetime.min.time())
    end_datetime = start_datetime + timedelta(hours=48)

    # Get the most recent instance ID among all those which are predicting in the required interval
    available_instance_ids = get_available_instance_ids(db, start_datetime, end_datetime).all()
    instance_id = available_instance_ids[0][0]

    # Get forecasts in this range
    query = get_forecasts(db, instance_id=instance_id, start_datetime=start_datetime, end_datetime=end_datetime)
    return all_or_404(query)


@router.get(
    "/forecast_geojson",
    description="Most up-to-date forecasts for a given day in GeoJSON",
    response_model=ForecastResultGeoJson,
)
async def forecast_geojson(
    date: date = Query(None, description="Date to retrieve forecasts for"),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:

    # Establish start and end datetimes
    start_datetime = datetime.combine(date, datetime.min.time())
    end_datetime = start_datetime + timedelta(hours=48)

    # Get the most recent instance ID among all those which are predicting in the required interval
    available_instance_ids = get_available_instance_ids(db, start_datetime, end_datetime).all()
    instance_id = available_instance_ids[0][0]

    # Get forecasts in this range
    query = get_forecasts_with_location(db, instance_id=instance_id, start_datetime=start_datetime, end_datetime=end_datetime)
    return all_or_404(query)
