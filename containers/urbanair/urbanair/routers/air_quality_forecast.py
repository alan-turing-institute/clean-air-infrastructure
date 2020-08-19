"""Air quality forecast API routes"""
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query
from ..databases import get_db
from ..databases.schemas.air_quality_forecast import (
    ForecastResultGeoJson,
    ForecastResultJson,
)
from ..databases.queries.air_quality_forecast import (
    cachable_available_instance_ids,
    cachable_forecasts_hexgridnogeom,
    cachable_forecasts_hexgridnogeom_bounded,
    cachable_forecasts_hexgrid,
    cachable_forecasts_hexgrid_bounded,
)
from ..responses import GeoJSONResponse


router = APIRouter()

# Define the bounding box for London
MIN_LONGITUDE = -0.510
MAX_LONGITUDE = 0.335
MIN_LATITUDE = 51.286
MAX_LATITUDE = 51.692


def bounding_box_params(
    lon_min: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, minimum longitude",
        example="-0.29875",
        ge=MIN_LONGITUDE,
        le=MAX_LONGITUDE,
    ),
    lon_max: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, maximum longitude",
        example="0.12375",
        ge=MIN_LONGITUDE,
        le=MAX_LONGITUDE,
    ),
    lat_min: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, minimum latitude",
        example="51.3875",
        ge=MIN_LATITUDE,
        le=MAX_LATITUDE,
    ),
    lat_max: Optional[float] = Query(
        None,
        description="[Optional] Bounding box, maximum latitude",
        example="51.5905",
        ge=MIN_LATITUDE,
        le=MAX_LATITUDE,
    ),
) -> Dict:
    """Common parameters in jamcam routes.
       If a camera_id is provided request up to 1 week of data
       If no camera_id is provided request up to 24 hours of data
    """
    # Ensure that all or none of the bounding box parameters are set
    if any([lon_min, lon_max, lat_min, lat_max]):
        # Longitude
        lon_min = lon_min if lon_min else MIN_LONGITUDE
        lon_max = lon_max if lon_max else MAX_LONGITUDE
        if lon_min >= lon_max:
            raise HTTPException(
                400,
                detail=f"Minimum longitude '{lon_min}' must be less than maximum '{lon_max}'",
            )
        # Latitude
        lat_min = lat_min if lat_min else MIN_LATITUDE
        lat_max = lat_max if lat_max else MAX_LATITUDE
        if lat_min >= lat_max:
            raise HTTPException(
                400,
                detail=f"Minimum latitude '{lat_min}' must be less than maximum '{lat_max}'",
            )

    return {
        "lon_min": lon_min,
        "lon_max": lon_max,
        "lat_min": lat_min,
        "lat_max": lat_max,
    }


@router.get(
    "/forecast/hexgrid/json",
    description="Most up-to-date forecasts for a given hour in JSON",
    response_model=List[ForecastResultJson],
)
def forecast_hexgrid_json(
    time_: datetime = Query(
        None,
        alias="time",
        description="JSON forecasts for the hour containing this ISO-formatted time",
        example="2020-08-12T06:00",
    ),
    db: Session = Depends(get_db),
    bounding_box: dict = Depends(bounding_box_params),
) -> Optional[List[Tuple]]:
    """Retrieve one hour of JSON forecasts containing the requested time

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        json: JSON containing one hour of forecasts at each hexgrid point
    """
    # Establish start and end datetimes
    start_datetime = time_.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

    # Get the most recent instance ID among those which predict in the required interval
    available_instance_ids = cachable_available_instance_ids(
        db, start_datetime, end_datetime
    )
    instance_id = available_instance_ids[0][0]

    # Get forecasts in this range (using a bounding box if specified)
    if all(bounding_box.values()):
        query_results = cachable_forecasts_hexgridnogeom_bounded(
            db,
            instance_id=instance_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            **bounding_box,
        )
    else:
        query_results = cachable_forecasts_hexgridnogeom(
            db,
            instance_id=instance_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

    # Return the query results as a list of tuples
    # This will be automatically converted to ForecastResultJson using from_orm
    return query_results


@router.get(
    "/forecast/hexgrid/geojson",
    description="Most up-to-date forecasts for a given hour in GeoJSON",
    response_class=GeoJSONResponse,
    response_model=ForecastResultGeoJson,
)
def forecast_hexgrid_geojson(
    time_: datetime = Query(
        None,
        alias="time",
        description="GeoJSON forecasts for the hour containing this ISO-formatted time",
        example="2020-08-12T06:00",
    ),
    db: Session = Depends(get_db),
    bounding_box: dict = Depends(bounding_box_params),
) -> Optional[List[Dict]]:
    """Retrieve one hour of GeoJSON forecasts containing the requested time

    Args:
        time (datetime): Time to retrieve forecasts for

    Returns:
        ForecastResultGeoJson: GeoJSON containing one hour of forecasts at each hexgrid point
    """
    # Establish start and end datetimes
    start_datetime = time_.replace(minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(hours=1)

    # Get the most recent instance ID among those which predict in the required interval
    available_instance_ids = cachable_available_instance_ids(
        db, start_datetime, end_datetime
    )
    instance_id = available_instance_ids[0][0]

    # Get forecasts in this range (using a bounding box if specified)
    if all(bounding_box.values()):
        query_results = cachable_forecasts_hexgrid_bounded(
            db,
            instance_id=instance_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            **bounding_box,
        )
    else:
        query_results = cachable_forecasts_hexgrid(
            db,
            instance_id=instance_id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

    # Return the query results as a GeoJSON FeatureCollection
    features = ForecastResultGeoJson.build_features(
        [r._asdict() for r in query_results]
    )
    return ForecastResultGeoJson(features=features)
