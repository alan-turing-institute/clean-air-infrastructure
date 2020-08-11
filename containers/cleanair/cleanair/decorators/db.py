"""DB decorators"""
from __future__ import annotations
import functools
import pandas as pd
from tabulate import tabulate

from typing import Callable, Any

class EmptyQueryError(Exception):
    """Raised when a database query returns no rows"""


def check_empty_df(data_frame: pd.DataFrame, raise_error: bool=True):
    """Check a dataframe is not empty and raise and error if it is"""
    if data_frame.empty and raise_error:
        raise EmptyQueryError(
            "The query returned no data. Check the query and ensure all required data is available"
        )


# pylint: disable=too-many-return-statements
def db_query(query_f: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrapper for functions that return an sqlalchemy query object.
    Args:
        output_type (str): Either 'query', 'subquery', 'df' or 'list'. list returns the first column of the query
    """

    @functools.wraps(query_f)
    def db_query_output(
        *args, output_type="query", limit=None, error_empty=False, **kwargs
    ):

        output_q = query_f(*args, **kwargs)

        if limit:
            output_q = output_q.limit(limit)

        if output_type == "df":
            data_frame = pd.read_sql(output_q.statement, output_q.session.bind)
            check_empty_df(data_frame, error_empty)
            return data_frame

        if output_type == "html":
            data_frame = pd.read_sql(output_q.statement, output_q.session.bind)
            check_empty_df(data_frame, error_empty)
            return data_frame.to_html()

        if output_type == "tabulate":
            data_frame = pd.read_sql(output_q.statement, output_q.session.bind)
            check_empty_df(data_frame, error_empty)
            return tabulate(data_frame, headers="keys", tablefmt="psq")

        if output_type == "list":
            query_df = pd.read_sql(output_q.statement, output_q.session.bind)
            return query_df[query_df.columns[0]].tolist()

        if output_type == "query":
            return output_q

        if output_type == "subquery":
            return output_q.subquery()

        if output_type == "count":
            return output_q.count()

        if output_type == "sql":
            return output_q.statement.compile(compile_kwargs={"literal_binds": True})

        raise ValueError("output_type {} is not valid".format(output_type))

    return db_query_output
