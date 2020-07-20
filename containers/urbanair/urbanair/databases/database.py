"""UrbanAir API database interactions"""
from typing import List, Dict, Optional
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query, Session
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.mixins import DBConnectionMixin
from ..config import get_settings


DB_SECRET_FILE = get_settings().db_secret_file
DB_CONNECTION_STRING = DBConnectionMixin(DB_SECRET_FILE)
DB_ENGINE = create_engine(DB_CONNECTION_STRING.connection_string, convert_unicode=True)
DeferredReflection.prepare(DB_ENGINE)
SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=DB_ENGINE)


# Dependency
def get_db() -> Session:
    "Get a database session"
    db = SESSION_LOCAL()
    try:
        yield db
    finally:
        db.close()


def all_or_404(query: Query) -> Optional[List[Dict]]:
    """
    Return all rows from a query and raise a 404 if empty
    """

    data = query.all()

    if len(data) > 0:
        return data

    raise HTTPException(404, detail="No data was found")
