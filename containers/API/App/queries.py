
from cleanair.mixins import DBConnectionMixin
import logging
from cleanair.loggers import get_log_level
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.ext.declarative import declarative_base
from cleanair.databases.base import Base
from cleanair.decorators import db_query
from cleanair.databases.tables import ModelResult, MetaPoint

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
                    func.ST_SetSRID(
                        func.ST_MAKEPoint(lon, lat), 4326
                    ),
                    0.001,
                ),
            ),
        )
        .order_by(
            func.ST_Distance(
                MetaPoint.location,
                func.ST_SetSRID(func.ST_MAKEPoint(lon, lat), 4326),
            )
        )
        .limit(1)
    )

    return closest_grid_point_q


@db_query
def get_point_forecast(session, lon, lat, max_dis=0.001):
    """Pass a lat lon and get the forecast for the closest forecast point"""
    closest_point_sq = get_closest_point(session, lon, lat, max_dist=0.001, output_type='subquery')

    return session.query(closest_point_sq.c.lon,
                         closest_point_sq.c.lat,
                         ModelResult.measurement_start_utc,
                         ModelResult.predict_mean,
                         ModelResult.predict_var).join(ModelResult)


@db_query
def get_all_forecasts(session, lon_min, lat_min, lon_max, lat_max):
    """Get all the scoot forecasts within a bounding box

    args:
        session: A session object
        bounding_box: A tuple of (lat_min, lon_min, lat_max, lon_max)"""

    interest_point_sq = session.query(func.ST_X(MetaPoint.location).label("lon"),
                                      func.ST_Y(MetaPoint.location).label("lat"),
                                      MetaPoint.id).filter(MetaPoint.source == "grid_100",
                                                           func.ST_Intersects(
                                                               MetaPoint.location,
                                                               func.ST_MakeEnvelope(
                                                                   lon_min, lat_min, lon_max, lat_max, 4326)
                                                           )).subquery()

    return session.query(interest_point_sq.c.lon,
                         interest_point_sq.c.lat,
                         ModelResult.measurement_start_utc,
                         ModelResult.predict_mean,
                         ModelResult.predict_var).join(ModelResult)
