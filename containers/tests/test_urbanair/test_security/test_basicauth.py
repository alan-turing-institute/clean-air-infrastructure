"""Basic auth security tests"""


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


def test_odysseus_basic_auth(client_odysseus_basic):
    """Test all paths on odysseus openapi spec have authentication"""
    api_spec = client_odysseus_basic.get("/openapi.json")
    paths = api_spec.json()["paths"]

    # For every path in the api spec assert that it is under basic auth
    for path in paths.keys():
        assert client_odysseus_basic.get(path).status_code == 401
        assert (
            client_odysseus_basic.get(path, auth=("local", "password")).status_code
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
