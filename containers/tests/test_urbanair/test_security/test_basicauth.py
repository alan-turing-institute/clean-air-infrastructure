"""Basic auth security tests"""


from fastapi.openapi.models import Header


def test_urbanair_basic_auth(client_urbanair_basic):
    """Test all paths on urbanair openapi spec have authentication"""
    api_spec = client_urbanair_basic.get("/openapi.json")
    paths = api_spec.json()["paths"]

    # For every path in the api spec assert that it is under basic auth
    for path in paths.keys():
        assert client_urbanair_basic.get(path).status_code == 401
        print(client_urbanair_basic.get(path, auth=("local", "password")))


def test_odysseus_basic_auth(client_odysseus_basic):
    """Test all paths on odysseus openapi spec have authentication"""
    api_spec = client_odysseus_basic.get("/openapi.json")
    paths = api_spec.json()["paths"]

    # For every path in the api spec assert that it is under basic auth
    for path in paths.keys():
        assert client_odysseus_basic.get(path).status_code == 401


def test_developer_basic_auth(client_developer_basic):
    """Test all paths on developer openapi spec have authentication"""
    api_spec = client_developer_basic.get("/openapi.json")
    paths = api_spec.json()["paths"]

    # For every path in the api spec assert that it is under basic auth
    for path in paths.keys():
        assert client_developer_basic.get(path).status_code == 401
