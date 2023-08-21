"""DB decorators"""
import functools
import pandas as pd
from tabulate import tabulate


class EmptyQueryError(Exception):
    """Raised when a database query returns no rows"""


def check_empty_df(data_frame, raise_error=True):
    """Check a dataframe is not empty and raise and error if it is"""
    if data_frame.empty and raise_error:
        raise EmptyQueryError(
            "The query returned no data. Check the query and ensure all required data is available"
        )


def db_query(model=None):
    """
    Wrapper for functions that return an SQLAlchemy query object.

    Args:
        model: A Pydantic model for data serialization to dict or JSON.
    """

    def _db_query(query_f):
        """
        Wrapper for functions that return an SQLAlchemy query object.

        Args:
            query_f: The function that returns an SQLAlchemy query object.
        """

        @functools.wraps(query_f)
        def db_query_output(
            *args, output_type="query", limit=None, error_empty=False, **kwargs
        ):
            # Get the SQLAlchemy query object from the wrapped function
            output_q = query_f(*args, **kwargs)

            # Apply limit if specified
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
                return output_q.statement.compile(
                    compile_kwargs={"literal_binds": True}
                )

            if output_type == "all":
                if model:
                    return [model.from_orm(i) for i in output_q]
                return output_q.all()

            raise ValueError(f"output_type '{output_type}' is not valid")

        return db_query_output

    return _db_query
