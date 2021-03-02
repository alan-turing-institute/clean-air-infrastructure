"""Get column names of a table"""

from typing import List
from sqlalchemy import inspect
from ..databases import Base


def get_columns_of_table(table: Base) -> List[str]:
    """Get the column names of a table."""
    table_inst = inspect(table)
    return [c_attr.key for c_attr in table_inst.mapper.column_attrs]
