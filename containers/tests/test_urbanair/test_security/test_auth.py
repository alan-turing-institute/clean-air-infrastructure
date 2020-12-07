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
def test_odysseus_oauth_session_redirect(client_odysseus_no_login, url):
    """Assert that all urls redirects to the login page when no session cookie present
    """

    request = client_odysseus_no_login.get(url, allow_redirects=False)

    assert request.status_code == 307
    assert request.headers["Location"] == "http://testserver/"


def test_odysseus_oauth_token(admin_token):
    "Test we can get a valid token when we are logged in (via dependency override) so we can get acccess token"

    # Validate the token and check username and roles
    payload = jwt.decode(
        admin_token[0],
        auth_settings.access_token_secret.get_secret_value(),
        algorithms=[auth_settings.access_token_algorithm],
    )
    username: str = payload.get("sub")
    roles = payload.get("roles", [])

    assert username == admin_token[1]
    assert roles == admin_token[2]


def test_odysseus_oauth_basic_paths(client_odysseus_logged_in_basic, basic_token):
    "Test basic user paths"
    client = client_odysseus_logged_in_basic[0]
    api_spec = client.get("/openapi.json", allow_redirects=False)
    paths = api_spec.json()["paths"]

    # print(basic_token)
    auth_headers = {"Authorization": f"Bearer {basic_token[0]}"}

    # For every path in the api spec assert that it is under bearer auth
    for path in paths.keys():

        for http_method, value in paths[path].items():

            assert len(value["security"]) == 1
            assert list(value["security"][0].keys())[0] == "HTTPBearer"

            if http_method == "get":
                unauth_response = client.get(path, allow_redirects=False)
                auth_response = client.get(
                    path, headers=auth_headers, allow_redirects=False
                )

            else:
                pytest.raises(NotImplementedError("Test not implemented"))

            print(
                "Path = {}, Method = {}, unauth_status = {}, auth_status = {}".format(
                    path,
                    http_method,
                    unauth_response.status_code,
                    auth_response.status_code,
                )
            )
            assert unauth_response.status_code == 403
            assert auth_response.status_code != 403


def test_odysseus_oauth_admin_only(
    client_odysseus_logged_in_admin, admin_token, basic_token
):

    client = client_odysseus_logged_in_admin[0]
    admin_headers = {"Authorization": f"Bearer {admin_token[0]}"}
    basic_headers = {"Authorization": f"Bearer {basic_token[0]}"}

    admin_response = client.get("/api/v1/jamcams/admin-check", headers=admin_headers)
    basic_response = client.get("/api/v1/jamcams/admin-check", headers=basic_headers)

    assert admin_response.status_code != 403
    assert basic_response.status_code == 403

    print(admin_response.content)
    print(basic_response.content)

