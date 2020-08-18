"""Air quality forecast API routes"""
from typing import List, Dict, Tuple, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Query
from ..databases import get_db
from ..databases.schemas.air_quality_forecast import (
    ForecastResultGeoJson,
    ForecastResultJson,
)
from ..databases.queries.air_quality_forecast import (
    cachable_available_instance_ids,
    cachable_forecasts,
    cachable_forecasts_geom,
)
from ..responses import GeoJSONResponse


router = APIRouter()


@router.get(
    "/forecast_json",
    description="Most up-to-date forecasts for a given day in JSON",
    response_model=List[ForecastResultJson],
)
def forecast_json(
    start_date: date = Query(None, description="Date to retrieve forecasts for"),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:
    """Retrieve 48hrs of JSON forecasts starting at midnight on the requested date"""

    # Establish start and end datetimes
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(hours=48)

    # Get the most recent instance ID among those which predict in the required interval
    available_instance_ids = cachable_available_instance_ids(
        db, start_datetime, end_datetime
    )
    instance_id = available_instance_ids[0][0]

    # Get forecasts in this range
    query_results = cachable_forecasts(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )

    # Return the query results as a list of tuples
    return query_results

    # One point: Finished after 1.1653501987457275 seconds
    # One point (cached): Finished after 2.8133392333984375e-05
    # All points: Finished after 10.618299961090088 seconds
    # All points (cached): Finished after 6.29425048828125e-05 seconds


@router.get(
    "/forecast_geojson",
    description="Most up-to-date forecasts for a given day in GeoJSON",
    response_class=GeoJSONResponse,
    response_model=ForecastResultGeoJson,
)
def forecast_geojson(
    start_date: date = Query(None, description="Date to retrieve forecasts for"),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:
    """Retrieve 48hrs of GeoJSON forecasts starting at midnight on the requested date"""

    # Establish start and end datetimes
    start_datetime = datetime.combine(start_date, datetime.min.time())
    end_datetime = start_datetime + timedelta(hours=48)

    # Get the most recent instance ID among those which predict in the required interval
    available_instance_ids = cachable_available_instance_ids(
        db, start_datetime, end_datetime
    )
    instance_id = available_instance_ids[0][0]

    # Get forecasts in this range
    query_results = cachable_forecasts_geom(
        db,
        instance_id=instance_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )

    # Return the query results as a GeoJSON FeatureCollection
    return ForecastResultGeoJson([r._asdict() for r in query_results])

    # One point: Finished after 1.1568198204040527 seconds
    # One point (cached): Finished after 6.67572021484375e-05 seconds
    # All points: Finished after 13.079823017120361 seconds
    # All points (cached): Finished after 0.5709922313690186 seconds
