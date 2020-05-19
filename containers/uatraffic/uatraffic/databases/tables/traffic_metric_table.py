"""Storing traffic metrics."""

from sqlalchemy import Column, Float, ForeignKey, String
from cleanair.databases import Base


class TrafficMetricTable(Base):
    """
    A table for storing metrics from traffic models.
    """

    __table_args__ = {"schema": "gla_traffic"}
    __tablename__ = "traffic_metric"

    instance_id = Column(
        String(64),
        ForeignKey("gla_traffic.traffic_instance.instance_id"),
        primary_key=True,
        nullable=False,
    )
    data_id = Column(
        String(64),
        ForeignKey("gla_traffic.traffic_data.data_id"),
        primary_key=True,
        nullable=False,
    )
    coverage50 = Column(Float, nullable=False, index=False)
    coverage75 = Column(Float, nullable=False, index=False)
    coverage95 = Column(Float, nullable=False, index=False)
    nlpl = Column(Float, nullable=False, index=False)

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table.columns]
        ]
        return "<Instance(" + ", ".join(vals)
