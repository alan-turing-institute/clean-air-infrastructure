"""Helper functions for reading secret files"""
import os

def read_basic_auth_secret(secret_directory = "/secrets", secret_file = 'basic_auth_password.txt'):
    """Read a basic auth secret"""

    full_secret_path = os.path.join(secret_directory, secret_file)
    with open(full_secret_path) as f_secret:
        passw = f_secret.read()
        if len(passw) > 0 and isinstance(passw, str):
            return passw
        raise IOError("Did not successfully load a non zero lenght password")