from flask import Blueprint, Response, render_template
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

index_bp = Blueprint("index", __name__)

auth = HTTPBasicAuth()
users = {
    "ati": generate_password_hash("colossus"),
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

@index_bp.route("/", methods=["GET"])
def index():
    resp = Response(
        """
<html>
    <head>
        <title>UrbanAir - The Alan Turing Institute</title>
    </head>
    <body>
        <h1>UrbanAir API</h1>
        <p>Welcome to the UrbanAir API developed by the Alan Turing Institute.</p>
        <p>The API provides 48 hour forecasts of air polution over London, UK</p>
    </body>
</html>""",
        mimetype="text/html",
    )
    return resp

@index_bp.route("/map", methods=["GET"])
@auth.login_required
def map():
    return render_template('map.html')