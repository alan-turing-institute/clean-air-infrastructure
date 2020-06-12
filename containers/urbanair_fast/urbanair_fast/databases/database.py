from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base
from cleanair.mixins import DBConnectionMixin
from ..config import get_settings


DB_SECRETS_FILE = get_settings().database_secret_file
DB_CONNECTION_STRING = DBConnectionMixin(DB_SECRETS_FILE)
DB_ENGINE = create_engine(DB_CONNECTION_STRING.connection_string, convert_unicode=True)
DeferredReflection.prepare(DB_ENGINE)
SESSION_LOCAL = sessionmaker(autocommit=False, autoflush=False, bind=DB_ENGINE)


# Dependency
def get_db():
    db = SESSION_LOCAL()
    try:
        yield db
    finally:
        db.close()
