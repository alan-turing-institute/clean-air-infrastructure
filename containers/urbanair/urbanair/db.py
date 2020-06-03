"""urbanair database configuration"""
from flask import current_app, g
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base

# A dict of sqlalchmy session factories
def configure_db_session():
    """Configure a connection to the cleanair database
    """

    # default to urbanair database
    uri = current_app.config["DATABASE_SECRETFILE"]
    db_connection_info = DBConnectionMixin(uri)

    engine = create_engine(db_connection_info.connection_string, convert_unicode=True)

    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )

    return db_session


def get_session():
    """Return a database session"""
    return current_app.config["DB_SESSIONS"]


def remove_db(exception=None):
    current_app.config["DB_SESSIONS"].remove()


def init_app():
    """Initilise the datase"""

    current_app.config["DB_SESSIONS"] = configure_db_session()
    current_app.teardown_appcontext(remove_db)
