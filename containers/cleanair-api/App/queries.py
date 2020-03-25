"""API database queries"""
from sqlalchemy import func
from cleanair.loggers import initialise_logging
from cleanair.decorators import db_query
from cleanair.databases.tables import (
    ModelResult,
    MetaPoint,
    ScootReading,
    ScootDetector,
)

initialise_logging(verbosity=0)


@db_query
def get_closest_point(session, lon, lat, max_dist=0.001):
    """Find the closest grid_100 point to a given lat lon location

    args:
        session: A sqlalchemy session object
        lon: Longitude
        lat: Latitude
        max_dist: Maximum distance to search in in degrees
    """

    # Find the closest point to the location
    closest_grid_point_q = (
        session.query(
            func.ST_X(MetaPoint.location).label("lon"),
            func.ST_Y(MetaPoint.location).label("lat"),
            MetaPoint.id,
        )
        .filter(
            MetaPoint.source == "grid_100",
            func.ST_Intersects(
                MetaPoint.location,
                func.ST_Expand(
                    func.ST_SetSRID(func.ST_MAKEPoint(lon, lat), 4326), max_dist,
                ),
            ),
        )
        .order_by(
            func.ST_Distance(
                MetaPoint.location, func.ST_SetSRID(func.ST_MAKEPoint(lon, lat), 4326),
            )
        )
        .limit(1)
    )

    return closest_grid_point_q


@db_query
def get_point_forecast(session, lon, lat, max_dist=0.001):
    """Pass a lat lon and get the forecast for the closest forecast point"""
    closest_point_sq = get_closest_point(
        session, lon, lat, max_dist=max_dist, output_type="subquery"
    )

    return (
        session.query(
            closest_point_sq.c.lon,
            closest_point_sq.c.lat,
            ModelResult.measurement_start_utc,
            ModelResult.predict_mean,
            ModelResult.predict_var,
        )
        .join(ModelResult)
        .filter(ModelResult.tag == "test_grid")
    )


@db_query
def get_all_forecasts(session, lon_min=None, lat_min=None, lon_max=None, lat_max=None):
    """Get all the scoot forecasts within a bounding box

    args:
        session: A session object
        bounding_box: A tuple of (lat_min, lon_min, lat_max, lon_max)"""

    ids_cte = (
        session.query(MetaPoint.id, MetaPoint.location)
        .filter(
            MetaPoint.source.in_(["grid_100",]),
            func.ST_Within(
                MetaPoint.location,
                func.ST_MakeEnvelope(lon_min, lat_min, lon_max, lat_max, 4326),
            ),
        )
        .cte("ids")
    )

    results_q = (
        session.query(
            func.ST_X(ids_cte.c.location).label("lon"),
            func.ST_Y(ids_cte.c.location).label("lat"),
            ModelResult.measurement_start_utc,
            ModelResult.predict_mean,
            ModelResult.predict_var,
        )
        .join(ModelResult, ids_cte.c.id == ModelResult.point_id, isouter=True)
        .filter(ModelResult.tag == "test_grid")
    )
    return results_q


@db_query
def get_scoot_with_location(session, start_time, end_time=None):
    """
    Get scoot data with lat and long positions
    """

    scoot_readings = (
        session.query(
            ScootReading.detector_id,
            func.ST_X(MetaPoint.location).label("lon"),
            func.ST_Y(MetaPoint.location).label("lat"),
            ScootReading.measurement_start_utc,
            ScootReading.measurement_end_utc,
            ScootReading.n_vehicles_in_interval,
            ScootReading.occupancy_percentage,
            ScootReading.congestion_percentage,
            ScootReading.saturation_percentage.label("saturation"),
        )
        .join(ScootDetector, ScootReading.detector_id == ScootDetector.detector_n)
        .join(MetaPoint, MetaPoint.id == ScootDetector.point_id)
        .filter(ScootReading.measurement_start_utc >= start_time)
    )

    if end_time:

        scoot_readings = scoot_readings.filter(
            ScootReading.measurement_start_utc < end_time
        )

    scoot_readings = scoot_readings.order_by(
        ScootReading.detector_id, ScootReading.measurement_start_utc
    )

    return scoot_readings
