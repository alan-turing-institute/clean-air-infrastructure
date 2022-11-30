"""
Tables for Breathe London data source
"""
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from ..base import Base


class BreatheSite(Base):
    """Table of Breathe sites"""
    
    __tablename__ = "breathe"
    __table_args__ = {"schema": "interest_points"}