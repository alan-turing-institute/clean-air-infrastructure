from sqlalchemy import Column, String, BigInteger, Text
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import TIMESTAMP

from ..base import Base


class Logs(Base):
    """Table of production logs"""

    __tablename__ = "logs"
    __table_args__ = {"schema": "logging"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    datetime = Column(TIMESTAMP)
    message = Column(Text())
