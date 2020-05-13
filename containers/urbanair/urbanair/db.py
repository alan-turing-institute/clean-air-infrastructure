"""urbanair database configuration"""
from flask import current_app, g
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base

# A dict of sqlalchmy session factories
def configure_db_session(db='urbanapi'):
    """Configure a connection to the cleanair database"""

    if db == 'jamcam':
        uri = current_app.config["DATABASE_SECRETFILE_JAMCAM"]
        db_connection_info = DBConnectionMixin(uri, allow_env_pass = False)
    else:
        # default to urbanair database
        uri = current_app.config["DATABASE_SECRETFILE"]
        db_connection_info = DBConnectionMixin(uri, allow_env_pass = True)

    engine = create_engine(
        db_connection_info.connection_string, convert_unicode=True
    )
    db_session = scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )
    return db_session

def get_session(db='urbanapi'):
    """Return a database session"""
    return current_app.config['DB_SESSIONS'][db]

def remove_db(exception=None):
    for _, sess in current_app.config['DB_SESSIONS'].items():
        sess.remove()

def init_app():
    """Initilise the datase"""
    db_sessions = {'urbanapi': configure_db_session('urbanapi'),
                   'jamcam': configure_db_session('jamcam')}

    current_app.config['DB_SESSIONS'] = db_sessions
    current_app.teardown_appcontext(remove_db)



