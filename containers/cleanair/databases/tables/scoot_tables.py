"""
Tables for SCOOT data source
"""
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.orm import relationship
from ..base import Base


class ScootReading(Base):
    """Table of Scoot readings"""

    __tablename__ = "scoot_reading"
    __table_args__ = {"schema": "dynamic_data"}

    detector_id = Column(
        String(9),
        ForeignKey("interest_points.scoot_detector.detector_n"),
        primary_key=True,
        nullable=False,
    )  # DETSCN
    measurement_start_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False
    )  # TIMESTAMP
    measurement_end_utc = Column(
        TIMESTAMP, primary_key=True, nullable=False
    )  # TIMESTAMP
    n_vehicles_in_interval = Column(Integer)  # FLOW_ACTUAL / 60
    occupancy_percentage = Column(DOUBLE_PRECISION)  # OCCU_ACTUAL
    congestion_percentage = Column(DOUBLE_PRECISION)  # CONG_ACTUAL
    saturation_percentage = Column(DOUBLE_PRECISION)  # SATU_ACTUAL
    flow_raw_count = Column(Integer)  # FLOW_COUNT
    occupancy_raw_count = Column(Integer)  # OCCU_COUNT
    congestion_raw_count = Column(Integer)  # CONG_COUNT
    saturation_raw_count = Column(Integer)  # SATU_COUNT
    region = Column(String(5))  # REGION

    # Create ScootReading.detector with no reverse relationship
    detector = relationship("ScootDetector")

    def __repr__(self):
        return "<ScootReading(" + ", ".join(
            [
                "detector_id='{}'".format(self.detector_id),
                "measurement_start_utc='{}'".format(self.measurement_start_utc),
                "measurement_end_utc='{}'".format(self.measurement_end_utc),
                "n_vehicles_in_interval='{}'".format(self.n_vehicles_in_interval),
                "occupancy_percentage='{}'".format(self.occupancy_percentage),
                "congestion_percentage='{}'".format(self.congestion_percentage),
                "saturation_percentage='{}'".format(self.saturation_percentage),
                "flow_raw_count='{}'".format(self.flow_raw_count),
                "occupancy_raw_count='{}'".format(self.occupancy_raw_count),
                "congestion_raw_count='{}'".format(self.congestion_raw_count),
                "saturation_raw_count='{}'".format(self.saturation_raw_count),
                "region='{}'".format(self.region),
            ]
        )


class ScootForecast(Base):
    """Table of Scoot forecasts"""

    __tablename__ = "scoot_forecast"
    __table_args__ = {"schema": "dynamic_data"}

    detector_id = Column(
        String(9),
        ForeignKey("interest_points.scoot_detector.detector_n"),
        primary_key=True,
        nullable=False,
    )
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    n_vehicles_in_interval = Column(Integer)
    occupancy_percentage = Column(DOUBLE_PRECISION)
    congestion_percentage = Column(DOUBLE_PRECISION)
    saturation_percentage = Column(DOUBLE_PRECISION)

    # Create ScootForecast.detector with no reverse relationship
    detector = relationship("ScootDetector")

    def __repr__(self):
        return "<ScootForecast(" + ", ".join(
            [
                "detector_id='{}'".format(self.detector_id),
                "measurement_start_utc='{}'".format(self.measurement_start_utc),
                "measurement_end_utc='{}'".format(self.measurement_end_utc),
                "n_vehicles_in_interval='{}'".format(self.n_vehicles_in_interval),
                "occupancy_percentage='{}'".format(self.occupancy_percentage),
                "congestion_percentage='{}'".format(self.congestion_percentage),
                "saturation_percentage='{}'".format(self.saturation_percentage),
            ]
        )

class ScootDetector(DeferredReflection, Base):
    """Table of Scoot detectors"""

    __tablename__ = "scoot_detector"
    __table_args__ = {"schema": "interest_points"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ScootDetector(" + ", ".join(vals)


class ScootRoadMatch(Base):
    """Table of all roads and their associated SCOOT sensors"""

    __tablename__ = "scoot_road_match"
    __table_args__ = {"schema": "dynamic_features"}

    road_toid = Column(
        String(),
        ForeignKey("static_data.oshighway_roadlink.toid"),
        primary_key=True,
        nullable=False,
    )
    detector_n = Column(
        String(),
        ForeignKey("interest_points.scoot_detector.detector_n"),
        primary_key=True,
        nullable=False,
    )
    distance_m = Column(DOUBLE_PRECISION, nullable=False)
    weight = Column(DOUBLE_PRECISION, nullable=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ScootRoadMatch(" + ", ".join(vals)


class ScootRoadForecast(Base):
    """Table of SCOOT forecasts for each road segment"""

    __tablename__ = "scoot_road_forecast"
    __table_args__ = {"schema": "dynamic_features"}

    road_toid = Column(
        String(),
        ForeignKey("static_data.oshighway_roadlink.toid"),
        primary_key=True,
        nullable=False,
    )
    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    measurement_end_utc = Column(TIMESTAMP, primary_key=True, nullable=False)
    n_vehicles_in_interval = Column(Integer)
    occupancy_percentage = Column(DOUBLE_PRECISION)
    congestion_percentage = Column(DOUBLE_PRECISION)
    saturation_percentage = Column(DOUBLE_PRECISION)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]
        ]
        return "<ScootRoadForecast(" + ", ".join(vals)
