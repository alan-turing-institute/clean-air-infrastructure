"""Declarative base class and table initialisation"""
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FromClause
from sqlalchemy.sql import table, column
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # pylint: disable=invalid-name


class Values(FromClause):
    named_with_column = True

    def __init__(self, columns, *args, **kw):
        self._column_args = columns
        self.list = args
        self.alias_name = self.name = kw.pop("alias_name", None)

    def _populate_column_collection(self):
        for c in self._column_args:
            c._make_proxy(self)

    @property
    def _from_objects(self):
        return [self]


@compiles(Values)
def compile_values(element, compiler, asfrom=False, **kw):
    columns = element.columns
    v = "VALUES %s" % ", ".join(
        "(%s)"
        % ", ".join(
            compiler.render_literal_value(elem, column.type)
            for elem, column in zip(tup, columns)
        )
        for tup in element.list
    )
    if asfrom:
        if element.alias_name:
            v = "(%s) AS %s (%s)" % (
                v,
                element.alias_name,
                (", ".join(c.name for c in element.columns)),
            )
        else:
            v = "(%s)" % v
    return v
