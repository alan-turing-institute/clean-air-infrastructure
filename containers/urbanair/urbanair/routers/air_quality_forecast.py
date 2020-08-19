"""Air quality forecast API routes"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
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
    "/forecast/hexgrid/json",
    description="Most up-to-date forecasts for a given hour in JSON",
    response_model=List[ForecastResultJson],
)
def forecast_json(
    time: datetime = Query(
        None,
        description="JSON forecasts for the hour containing this time (in ISO-format eg. 2020-08-12T06:00)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Tuple]]:
    """Retrieve one hour of JSON forecasts containing the requested time

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        json: JSON containing one hour of forecasts at each hexgrid point
    """
    # Establish start and end datetimes
    start_datetime = time.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

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


@router.get(
    "/forecast/hexgrid/geojson",
    description="Most up-to-date forecasts for a given hour in GeoJSON",
    response_class=GeoJSONResponse,
    response_model=ForecastResultGeoJson,
)
def forecast_geojson(
    time: datetime = Query(
        None,
        description="GeoJSON forecasts for the hour containing this time (in ISO-format eg. 2020-08-12T06:00)",
    ),
    db: Session = Depends(get_db),
) -> Optional[List[Dict]]:
    """Retrieve one hour of GeoJSON forecasts containing the requested time

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        ForecastResultGeoJson: GeoJSON containing one hour of forecasts at each hexgrid point
    """
    # Establish start and end datetimes
    start_datetime = time.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

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
