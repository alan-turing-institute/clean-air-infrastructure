"""Functions for authenticating to the database"""

import json
import subprocess

from ..exceptions import (
    DatabaseAccessTokenException,
    DatabaseUserAuthenticationException,
)

DATABASE_NAME = "cleanair-inputs-2021-server"


def get_database_username() -> str:
    """Get the Azure username"""
    try:
        user_cmd = subprocess.run(
            ["az", "ad", "signed-in-user", "show", "-o", "json"],
            capture_output=True,
            check=True,
        )
        username = json.loads(user_cmd.stdout.decode())["userPrincipalName"]
    except Exception as exc:
        raise DatabaseUserAuthenticationException() from exc
    return username + "@" + DATABASE_NAME


def get_database_access_token() -> str:
    """Get the access token for a user of the Azure database"""
    try:
        token_cmd = subprocess.run(
            [
                "az",
                "account",
                "get-access-token",
                "--resource-type",
                "oss-rdbms",
                "--query",
                "accessToken",
                "-o",
                "tsv",
            ],
            check=True,
            capture_output=True,
        )
    except Exception as exc:
        raise DatabaseAccessTokenException() from exc
    token = token_cmd.stdout.decode("utf-8")[:-1]
    return token
