"""urbanair database configuration"""
from flask import current_app, g
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base


def configure_db_session(db='urbanapi'):
    """Configure a connection to the cleanair database"""
    # if "db_session" not in g:
    #  Configure session

    # default to urbanair database
    uri = current_app.config["DATABASE_URI"]
    if db == 'jamcam':
        uri = current_app.config["DATABASE_URI_JAMCAM"]

    db_connection_info = DBConnectionMixin(uri) # TODO@Oscar Should work when jamcam URI in secrets
    engine = create_engine(
        db_connection_info.connection_string, convert_unicode=True
        # connection_string, convert_unicode=True
    )
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    # DeferredReflection.prepare(engine)
    # Base.query = db_session.query_property()

    # g.db_session = db_session

    # return g.db_session
    return db_session


# pylint: disable=C0103

# Deprecated if no globals
# def remove_db(e=None):
    # db_session = g.pop("db_session", None)
    # if db_session:
    #     db_session.remove()


def get_session(db="urbanair"):
    db_session = configure_db_session(db)
    return db_session()


def init_app(app):
    configure_db_session('jamcam')
    # app.teardown_appcontext(remove_db)
