"""
Table for UKMap static data
"""
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, DATE
from geoalchemy2 import Geometry # type: ignore
from ..base import Base


class UKMap(Base):
    """Table of static UKMap data"""

    __tablename__ = "ukmap"
    __table_args__ = {"schema": "static_data"}

    geographic_type_number = Column(Integer, primary_key=True, nullable=False,)
    date_of_feature_edit = Column(DATE)
    feature_type = Column(String(200), index=True)
    landuse = Column(String(200), index=True)
    postcode = Column(String(200))
    height_of_base_of_building = Column(DOUBLE_PRECISION)
    calculated_height_of_building = Column(DOUBLE_PRECISION)
    geom_length = Column(DOUBLE_PRECISION)
    geom_area = Column(DOUBLE_PRECISION)
    geom = Column(Geometry(srid=4326, spatial_index=True))

    def __repr__(self) -> str:
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<UKMap(" + ", ".join(vals) + ")>"
