"""API decorators"""
import functools
import time
import logging
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
