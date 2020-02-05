"""API database queries"""
import logging
from sqlalchemy import func
from cleanair.loggers import get_log_level
from cleanair.decorators import db_query
from cleanair.databases.tables import ModelResult, MetaPoint, User

logging.basicConfig(level=get_log_level(0))


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

    return session.query(
        closest_point_sq.c.lon,
        closest_point_sq.c.lat,
        ModelResult.measurement_start_utc,
        ModelResult.predict_mean,
        ModelResult.predict_var,
    ).join(ModelResult)


@db_query
def get_all_forecasts(session, lon_min=None, lat_min=None, lon_max=None, lat_max=None):
    """Get all the scoot forecasts within a bounding box

    args:
        session: A session object
        bounding_box: A tuple of (lat_min, lon_min, lat_max, lon_max)"""

    interest_point_q = session.query(
        func.ST_X(MetaPoint.location).label("lon"),
        func.ST_Y(MetaPoint.location).label("lat"),
        MetaPoint.id,
    ).filter(MetaPoint.source == "grid_100")

    if lon_min and lat_min and lon_max and lat_max:
        interest_point_q = interest_point_q.filter(
            func.ST_Intersects(
                MetaPoint.location,
                func.ST_MakeEnvelope(lon_min, lat_min, lon_max, lat_max, 4326),
            )
        )

    interest_point_sq = interest_point_q.subquery()

    latest_model_result_sq = session.query(
        func.max(ModelResult.fit_start_time).label("latest_forecast")
    ).subquery()

    return (
        session.query(
            interest_point_sq.c.lon,
            interest_point_sq.c.lat,
            ModelResult.measurement_start_utc,
            ModelResult.predict_mean,
            ModelResult.predict_var,
        )
        .join(ModelResult)
        .filter(ModelResult.fit_start_time == latest_model_result_sq.c.latest_forecast)
    )
