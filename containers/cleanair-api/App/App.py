"""CleanAir API Application"""
# pylint: skip-file
from flask import Flask, Response, jsonify
from flask_marshmallow import Marshmallow
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base
from .queries import get_point_forecast, get_all_forecasts
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser, abort


# Initialise application
app = Flask(__name__)
ma = Marshmallow(app)

# Configure session
DB_CONNECTION_INFO = DBConnectionMixin("db_secrets.json")
engine = create_engine(DB_CONNECTION_INFO.connection_string, convert_unicode=True)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
DeferredReflection.prepare(engine)
Base.query = db_session.query_property()

# Return validation errors as JSON
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return jsonify({"errors": messages}), err.code, headers
    else:
        return jsonify({"errors": messages}), err.code


# Ensure sessions are closed by flask
@app.teardown_appcontext
def shutdown_session(exception=None):
    """Close down database connections"""
    db_session.remove()


class Results(ma.Schema):
    """Mapping for API query results"""

    class Meta:
        fields = [
            "lat",
            "lon",
            "measurement_start_utc",
            "predict_mean",
            "predict_var",
        ]


results = Results(many=True)


@app.route("/", methods=["GET"])
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


@app.route("/api/v1/point")
@use_args(
    {"lat": fields.Float(required=True), "lon": fields.Float(required=True)},
    location="query",
)
def point(args):
    """CleanAir API Point request
    
    Example:
    To request data at the Turing institute
    pip install httpie
    http --download GET :5000/api/v1/point lat==51.5309 lon==-0.1267
    or with curl:
    curl 'localhost:5000/api/v1/point?lat=51.5309&lon=-0.1267'
    """
    session = db_session()
    points_forecast = get_point_forecast(
        session, args["lon"], args["lat"], output_type="query"
    )
    return jsonify(results.dump(points_forecast))


@app.route("/api/v1/box", methods=["GET"])
@use_args(
    {
        "lonmin": fields.Float(required=True),
        "lonmax": fields.Float(required=True),
        "latmin": fields.Float(required=True),
        "latmax": fields.Float(required=True),
    },
    location="query",
)
def box(args):
    """CleanAir API Point request
    
    Example:
    To request forecast at all points within a bounding box over city hall
    pip install httpie
    http  --download GET :5000/api/v1/box lonmin==-0.10653288909912088 latmin==51.49361775468337 lonmax==-0.050657110900877635 latmax==51.515949509214245
    or with curl:
    curl 'localhost:5000/api/v1/box?lonmin=-0.10653288909912088&latmin=51.49361775468337&lonmax=-0.050657110900877635&ylatmax=51.515949509214245'
    """
    session = db_session()
    all_points = get_all_forecasts(
        session,
        args["lonmin"],
        args["latmin"],
        args["lonmax"],
        args["latmax"],
        output_type="query",
    )

    return jsonify(results.dump(all_points))


if __name__ == "__main__":
    app.run(host="0.0.0.0")
