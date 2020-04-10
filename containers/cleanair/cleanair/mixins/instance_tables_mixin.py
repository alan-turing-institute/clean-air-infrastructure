"""
Table that summerises an instance (model + data + result).
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import TIMESTAMP

class InstanceTableMixin:
    """Table of Instances."""

    __tablename__ = "instance"

    instance_id = Column(String(64), primary_key=True, nullable=False)
    model_name = Column(
        String(64),
        nullable=False,
        index=False,
    )
    tag = Column(String(64), nullable=False, index=False)
    param_id = Column(
        String(64),
        nullable=False,
        index=False,
    )
    data_id = Column(
        String(64),
        nullable=False,
        index=False,
    )
    git_hash = Column(String(40), nullable=False, index=False)
    fit_start_time = Column(TIMESTAMP, primary_key=False, nullable=False)
    cluster_id = Column(String(64), nullable=False, index=False)
