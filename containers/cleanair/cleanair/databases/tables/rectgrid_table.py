"""
Tables for AQE data source
"""
from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import DeferredReflection
from ..base import Base


class RectGrid(Base):
    """Table of grid points"""

    __tablename__ = "rectgrid"
    __table_args__ = {"schema": "interest_points"}

    column_id = Column(Integer, primary_key=True, nullable=False)
    row_id = Column(Integer, primary_key=True, nullable=False)
    point_id = Column(UUID, ForeignKey("interest_points.meta_point.id"), nullable=False)
    geom = Column(
        Geometry(geometry_type="POLYGON", srid=4326, dimension=2, spatial_index=True)
    )

    # Create RectGrid.point with no reverse relationship
    point = relationship("MetaPoint")

    def __repr__(self):
        return (
            "<RectGrid("
            + ", ".join(
                [
                    "column_id='{}'".format(self.column_id),
                    "row_id='{}'".format(self.row_id),
                    "point_id='{}'".format(self.point_id),
                    "geom='{}'".format(self.geom),
                ]
            )
            + ")>"
        )

    @staticmethod
    def build_entry(gridcell_dict):
        """Create a RectGrid entry and return it"""
        return RectGrid(
            column_id=gridcell_dict["column_id"],
            row_id=gridcell_dict["row_id"],
            point_id=str(gridcell_dict["point_id"]),
            geom=gridcell_dict["geom"],
        )


class RectGrid100(DeferredReflection, Base):
    """Table of 100m grid points"""

    __tablename__ = "rectgrid_100"
    __table_args__ = {"schema": "interest_points"}

    def __repr__(self):
        vals = [
            "{}='{}'".format(column, getattr(self, column))
            for column in [c.name for c in self.__table__.columns]  # pylint: disable=no-member
        ]
        return "<RectGrid100(" + ", ".join(vals) + ")>"
