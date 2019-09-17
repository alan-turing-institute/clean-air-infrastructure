from sqlalchemy import DDL, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import DeferredReflection

Base = declarative_base()  # pylint: disable=invalid-name
SCHEMA_NAMES = ['datasources', 'buffers', 'modelfits']
EVENTS = [event.listen(Base.metadata, 'before_create',
                       DDL("CREATE SCHEMA IF NOT EXISTS {}".format(schema))) for schema in SCHEMA_NAMES]

def initialise_tables(engine):
    """Ensure that all tables exist"""
    # Create reflected tables first as these already exist
    DeferredReflection.prepare(engine)
    # Next create all other tables
    Base.metadata.create_all(engine, checkfirst=True)
