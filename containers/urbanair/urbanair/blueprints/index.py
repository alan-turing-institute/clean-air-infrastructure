from flask import Blueprint, Response


index_bp = Blueprint('index', __name__)


@index_bp.route('/', methods=['GET'])
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
