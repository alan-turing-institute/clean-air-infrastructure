"""Clean air decorators"""
import functools
import time
import logging
import pandas as pd
import requests
from ..loggers import get_logger

logging.basicConfig(level=20)
logger = get_logger(__name__)  # pylint: disable=C0103


def robust_api(api_call):
    """Wrapper function for making multiple calls to the same API endpoint to overcome server errors
       kwargs:
            n_repeat: Maximum number of calls to the API that can be made
            sleep_time: Time to sleep between api calls in seconds
    """

    @functools.wraps(api_call)
    def robust_api_output(*args, n_repeat=10, sleep_time=3, **kwargs):

        for i in range(n_repeat):
            logger.debug("Making API request attempt %s out of %s", i, n_repeat)
            try:
                return api_call(*args, **kwargs)

            except requests.exceptions.HTTPError:
                if i < n_repeat:
                    logger.warning(
                        "Failed to make API request. Sleeping for %s seconds before next attempt",
                        sleep_time,
                    )
                    time.sleep(sleep_time)

                else:
                    raise requests.exceptions.HTTPError

    return robust_api_output


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
