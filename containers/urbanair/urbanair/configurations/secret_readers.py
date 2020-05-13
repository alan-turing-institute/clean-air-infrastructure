"""Helper functions for reading secret files"""

def read_basic_auth_secret(location = 'secrets/BASIC_AUTH_PASSWORD'):
    """Read a basic auth secret"""
    with open(location) as f_secret:
        return f_secret.read()