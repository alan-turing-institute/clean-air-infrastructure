"""DB decorators"""
import functools
import pandas as pd


def db_query(query_f):
    """Wrapper for functions that return an sqlalchemy query object.
    kwargs:
        output_type: Either 'query', 'subquery', 'df' or 'list'. list returns the first column of the query
    """

    @functools.wraps(query_f)
    def db_query_output(*args, output_type="query", limit=None, **kwargs):

        output_q = query_f(*args, **kwargs)

        if limit:
            output_q = output_q.limit(limit)

        if output_type == "df":
            return pd.read_sql(output_q.statement, output_q.session.bind)

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
