"""Impliment HTTPBasicAuth"""

from flask import current_app
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash

http_auth = HTTPBasicAuth()

@http_auth.verify_password
def verify_password(username, password):
    if username in current_app.config['USERS'] and \
            check_password_hash(current_app.config['USERS'].get(username), password):
        
        return username