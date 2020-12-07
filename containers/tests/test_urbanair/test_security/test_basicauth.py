"""Basic auth security tests"""
from jose import jwt
import pytest
from urbanair.security.oath import auth_settings


def test_urbanair_basic_auth(client_urbanair_basic):
    """Test all paths on urbanair openapi spec have authentication"""

    api_spec = client_urbanair_basic.get("/openapi.json")
    paths = api_spec.json()["paths"]

    # For every path in the api spec assert that it is under basic auth
    for path in paths.keys():

        # Check unauthenticated errors with 401
        assert client_urbanair_basic.get(path).status_code == 401
        # Check authenticated passes or fails with another status code
        assert (
            client_urbanair_basic.get(path, auth=("local", "password")).status_code
            != 401
        )


def test_developer_basic_auth(client_developer_basic):
    """Test all paths on developer openapi spec have authentication"""
    api_spec = client_developer_basic.get("/openapi.json")
    paths = api_spec.json()["paths"]

    # For every path in the api spec assert that it is under basic auth
    for path in paths.keys():
        assert client_developer_basic.get(path).status_code == 401
        assert (
            client_developer_basic.get(path, auth=("local", "password")).status_code
            != 401
        )


@pytest.mark.parametrize("url", ["/user", "/auth/token", "/logout", "/usage", "/map"])
def test_odysseus_oauth_session_redirect(client_odysseus_no_loggin, url):
    """Assert that all urls redirects to the login page when no session cookie present
    """

    request = client_odysseus_no_loggin.get(url, allow_redirects=False)

    assert request.status_code == 307
    assert request.headers["Location"] == "http://testserver/"


def test_odysseus_oauth_token(client_odysseus_login):

    url = "/auth/token"
    request = client_odysseus_login[0].get(url, allow_redirects=False)

    assert request.status_code == 200

    token = request.json()["access_token"]
    payload = jwt.decode(
        token,
        auth_settings.access_token_secret.get_secret_value(),
        algorithms=[auth_settings.access_token_algorithm],
    )
    username: str = payload.get("sub")
    roles = payload.get("roles", [])

    assert username == client_odysseus_login[1]
    assert roles == client_odysseus_login[2]
