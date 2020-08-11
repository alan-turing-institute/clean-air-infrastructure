"""
Taken from sqlalchemy utils - minor adjustments required to source code
to allow for using different schemas and checking that materialized views
exist before creating them

Copyright (c) 2012, Konsta Vesterinen

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* The names of the contributors may not be used to endorse or promote products
  derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
# Dont pylint as from sqlalchemy_utils
# pylint: skip-file

import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.schema import DDLElement, PrimaryKeyConstraint
from geoalchemy2.types import Geometry


class RawGeometry(Geometry):
    # Override Geometry type so it doesnt wrap with st_AsEWKB
    def column_expression(self, col):
        return col


class CreateView(DDLElement):
    def __init__(self, name, schema, selectable, materialized=False):
        self.name = name
        self.schema = schema
        self.selectable = selectable
        self.materialized = materialized


@compiler.compiles(CreateView)
def compile_create_materialized_view(element, compiler, **kw):
    return "CREATE {}VIEW IF NOT EXISTS {}.{} AS {}".format(
        "MATERIALIZED " if element.materialized else "",
        element.schema,
        element.name,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


class SetViewOwner(DDLElement):
    def __init__(self, name, owner, materialized=False):
        self.name = name
        self.owner = owner
        self.materialized = materialized


@compiler.compiles(SetViewOwner)
def compile_set_view_owner(element, compiler, **kw):
    return "ALTER {} VIEW {} OWNER TO {}".format(
        "MATERIALIZED " if element.materialized else "",
        element.name,
        element.owner,
        compiler.sql_compiler.process(element.selectable, literal_binds=True),
    )


def create_table_from_selectable(
    name, selectable, schema, indexes=None, metadata=None, aliases=None
):
    if indexes is None:
        indexes = []
    if metadata is None:
        metadata = sa.MetaData()
    if aliases is None:
        aliases = {}
    args = [
        sa.Column(
            c.name, c.type, key=aliases.get(c.name, c.name), primary_key=c.primary_key
        )
        for c in selectable.c
    ] + indexes
    table = sa.Table(name, metadata, *args, schema=schema)

    if not any([c.primary_key for c in selectable.c]):
        table.append_constraint(PrimaryKeyConstraint(*[c.name for c in selectable.c]))
    return table


def create_materialized_view(
    name, selectable, metadata, indexes=None, aliases=None, schema="public", owner=None
):
    """ Create a view on a given metadata

    :param name: The name of the view to create.
    :param selectable: An SQLAlchemy selectable e.g. a select() statement.
    :param metadata:
        An SQLAlchemy Metadata instance that stores the features of the
        database being described.
    :param indexes: An optional list of SQLAlchemy Index instances.
    :param aliases:
        An optional dictionary containing with keys as column names and values
        as column aliases.

    Same as for ``create_view`` except that a ``CREATE MATERIALIZED VIEW``
    statement is emitted instead of a ``CREATE VIEW``.

    """
    table = create_table_from_selectable(
        name=name,
        schema=schema,
        selectable=selectable,
        indexes=indexes,
        metadata=None,
        aliases=aliases,
    )

    sa.event.listen(
        metadata,
        "after_create",
        CreateView(name, schema, selectable, materialized=True),
    )

    @sa.event.listens_for(metadata, "after_create")
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    if owner:

        @sa.event.listens_for(metadata, "after_create")
        def set_owner(target, connection, **kw):
            SetViewOwner(name=name, owner=owner, materialized=True)

    return table


def create_view(name, selectable, metadata, cascade_on_drop=True):
    """ Create a view on a given metadata

    :param name: The name of the view to create.
    :param selectable: An SQLAlchemy selectable e.g. a select() statement.
    :param metadata:
        An SQLAlchemy Metadata instance that stores the features of the
        database being described.

    The process for creating a view is similar to the standard way that a
    table is constructed, except that a selectable is provided instead of
    a set of columns. The view is created once a ``CREATE`` statement is
    executed against the supplied metadata (e.g. ``metadata.create_all(..)``),
    and dropped when a ``DROP`` is executed against the metadata.

    To create a view that performs basic filtering on a table. ::

        metadata = MetaData()
        users = Table('users', metadata,
                Column('id', Integer, primary_key=True),
                Column('name', String),
                Column('fullname', String),
                Column('premium_user', Boolean, default=False),
            )

        premium_members = select([users]).where(users.c.premium_user == True)
        create_view('premium_users', premium_members, metadata)

        metadata.create_all(engine) # View is created at this point

    """
    table = create_table_from_selectable(
        name=name, selectable=selectable, metadata=None
    )

    sa.event.listen(metadata, "after_create", CreateView(name, selectable))

    @sa.event.listens_for(metadata, "after_create")
    def create_indexes(target, connection, **kw):
        for idx in table.indexes:
            idx.create(connection)

    sa.event.listen(metadata, "before_drop", DropView(name, cascade=cascade_on_drop))
    return table


def refresh_materialized_view(session, name, concurrently=False):
    """ Refreshes an already existing materialized view

    :param session: An SQLAlchemy Session instance.
    :param name: The name of the materialized view to refresh.
    :param concurrently:
        Optional flag that causes the ``CONCURRENTLY`` parameter
        to be specified when the materialized view is refreshed.
    """
    # Since session.execute() bypasses autoflush, we must manually flush in
    # order to include newly-created/modified objects in the refresh.
    session.flush()
    session.execute(
        "REFRESH MATERIALIZED VIEW {}{}".format(
            "CONCURRENTLY " if concurrently else "", name
        )
    )
