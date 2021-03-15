"HTTP Basic authorization"
import logging
from passlib.apache import HtpasswdFile
from cachetools import cached, TTLCache
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from ..config import get_settings

# pylint: disable=invalid-name
logger = logging.getLogger("fastapi")
security = HTTPBasic()


@cached(cache=TTLCache(maxsize=256, ttl=3600))
def get_http_passwords() -> HtpasswdFile:
    "Load a htpasswdfile from disk"

    return HtpasswdFile(get_settings().htpasswdfile)


def get_http_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    "Get username from http basic auth and check authorization. Raise 401 is not authenticated"
    ht = get_http_passwords()
    correct_username_and_password = ht.check_password(
        credentials.username, credentials.password
    )

    if not correct_username_and_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
