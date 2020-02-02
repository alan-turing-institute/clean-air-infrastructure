"""Declarative base class and table initialisation"""
from sqlalchemy import DDL, event, Table, MetaData, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement, PrimaryKeyConstraint

Base = declarative_base()  # pylint: disable=invalid-name
SCHEMA_NAMES = [
    "dynamic_data",
    "dynamic_features",
    "interest_points",
    "static_data",
    "static_features",
    "model_results",
]

EVENTS = [
    event.listen(
        Base.metadata,
        "before_create",
        DDL("CREATE SCHEMA IF NOT EXISTS {}".format(schema)),
    )
    for schema in SCHEMA_NAMES
]


# Create Materialized views
class CreateMaterializedView(DDLElement):
    def __init__(self, name, selectable):
        self.name = name
        self.selectable = selectable


@compiler.compiles(CreateMaterializedView)
def compile_(element, compiler, **kwargs):
    # Could use "CREATE OR REPLACE MATERIALIZED VIEW..."
    # but I'd rather have noisy errors
    return "CREATE MATERIALIZED VIEW IF NOT EXISTS %s AS %s" % (
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


def create_mat_view(metadata, name, selectable):
    _mt = MetaData()  # temp metadata just for initial Table object creation
    t = Table(name, _mt, quote=False)  # the actual mat view class is bound to db.metadata
    for c in selectable.c:
        t.append_column(Column(c.name, c.type, primary_key=c.primary_key, quote=None))

    if not (any([c.primary_key for c in selectable.c])):
        t.append_constraint(PrimaryKeyConstraint(*[c.name for c in selectable.c]))

    event.listen(
        metadata, "after_create",
        CreateMaterializedView(name, selectable)
    )

    @event.listens_for(metadata, "after_create")
    def create_indexes(target, connection, **kwargs):
        for idx in t.indexes:
            idx.create(connection)

    event.listen(
        metadata, "before_drop",
        DDL('DROP MATERIALIZED VIEW IF EXISTS ' + name)
    )
    return t
