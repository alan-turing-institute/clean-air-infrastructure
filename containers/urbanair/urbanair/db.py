from flask import current_app, g
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base


def configure_db_session():

    if 'db_session' not in g:
        #  Configure session
        DB_CONNECTION_INFO = DBConnectionMixin(current_app.config['DATABASE_URI'])
        engine = create_engine(DB_CONNECTION_INFO.connection_string, convert_unicode=True)
        db_session = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=engine)
        )
        DeferredReflection.prepare(engine)
        Base.query = db_session.query_property()
        g.db_session = db_session

    return g.db_session


def remove_db(e=None):
    db_session = g.pop('db_session', None)
    if db_session:
        db_session.remove()


def get_session():

    db_session = configure_db_session()
    return db_session()


def init_app(app):
    configure_db_session()
    app.teardown_appcontext(remove_db)
