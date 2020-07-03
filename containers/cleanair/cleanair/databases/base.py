"""Declarative base class and table initialisation"""
from sqlalchemy.ext.compiler import compiles # type: ignore
from sqlalchemy.sql.expression import FromClause # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore

Base = declarative_base()  # pylint: disable=invalid-name


class Values(FromClause):
    """Create SQL for values within a query"""

    named_with_column = True

    # pylint: disable=unused-argument
    def __init__(self, columns, *args, **kw):
        self._column_args = columns
        self.list = args
        self.alias_name = self.name = kw.pop("alias_name", None)

    def _populate_column_collection(self):
        # pylint: disable=protected-access
        for col in self._column_args:
            col._make_proxy(self)

    @property
    def _from_objects(self):
        return [self]


@compiles(Values)
# pylint: disable=unused-argument
def compile_values(element, compiler, asfrom=False, **kw):
    """Compile values to sql"""
    # pylint: disable=invalid-name
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
