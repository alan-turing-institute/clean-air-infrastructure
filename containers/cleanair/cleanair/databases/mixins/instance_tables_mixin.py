"""
Table that summerises an instance (model + data + result).
"""

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB, UUID


class InstanceTableMixin:
    """Table of Instances."""

    instance_id = Column(String(64), primary_key=True, nullable=False)
    tag = Column(String(64), nullable=False, index=False)
    git_hash = Column(String(40), nullable=False, index=False)
    fit_start_time = Column(TIMESTAMP, primary_key=False, nullable=False)
    cluster_id = Column(String(64), nullable=False, index=False)
    model_name = Column(String(64), nullable=False, index=False)
    param_id = Column(String(64), nullable=False, index=False)
    data_id = Column(String(64), nullable=False, index=False)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]  # pylint: disable=no-member
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<" + self.__tablename__ + "(" + ", ".join(vals)


class ModelTableMixin:
    """Table of model parameters."""

    model_name = Column(String(64), primary_key=True, nullable=False)
    param_id = Column(String(64), primary_key=True, nullable=False)
    model_params = Column(JSONB, nullable=False, index=True)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<" + self.__tablename__ + "(" + ", ".join(vals)


class DataTableMixin:
    """Table of model parameters."""

    data_id = Column(String(64), primary_key=True, nullable=False)
    # we might be able to build an index on certain keys, but not the whole column :(
    data_config = Column(JSONB, nullable=False, index=False)
    preprocessing = Column(JSONB, nullable=False, index=False)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<" + self.__tablename__ + "(" + ", ".join(vals)


class MetricsTableMixin:
    """Table for model metrics."""

    instance_id = Column(String(64), primary_key=True, nullable=False)
    data_id = Column(String(64), primary_key=True, nullable=False)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]  # pylint: disable=no-member
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<" + self.__tablename__ + "(" + ", ".join(vals)


class ResultTableMixin:
    """Table mixin for model results."""

    instance_id = Column(String(64), primary_key=True, nullable=False)
    data_id = Column(String(64), primary_key=True, nullable=False)

    @classmethod
    @declared_attr
    def point_id(cls):
        """Point id of the meta point schema."""
        return Column(
            UUID,
            ForeignKey("interest_points.meta_point.id"),
            primary_key=True,
            nullable=False,
        )

    measurement_start_utc = Column(TIMESTAMP, primary_key=True, nullable=False)

    def __repr__(self):
        cols = [c.name for c in self.__table__.columns]  # pylint: disable=no-member
        vals = ["{}='{}'".format(column, getattr(self, column)) for column in cols]
        return "<" + self.__tablename__ + "(" + ", ".join(vals)
