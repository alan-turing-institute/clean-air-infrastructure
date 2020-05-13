"""Helper functions for reading secret files"""

def read_basic_auth_secret(location = 'secrets/basic_auth_password.txt'):
    """Read a basic auth secret"""
    with open(location) as f_secret:
        return f_secret.read()