"""CleanAir API Application"""
# pylint: skip-file
from flask import Flask, url_for
from flask_restful import Resource, Api, abort
from flask_marshmallow import Marshmallow
from flask_httpauth import HTTPBasicAuth
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base
from webargs import fields
from webargs.flaskparser import use_args
from .queries import get_point_forecast, get_all_forecasts, check_user_exists, create_user


# Initialise application
auth = HTTPBasicAuth()
app = Flask(__name__)
ma = Marshmallow(app)
api = Api(app)

# Configure session
DB_CONNECTION_INFO = DBConnectionMixin(
    "/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets-offline.json")
engine = create_engine(DB_CONNECTION_INFO.connection_string, convert_unicode=True)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
DeferredReflection.prepare(engine)
Base.query = db_session.query_property()

Base.metadata.create_all(engine, checkfirst=True)

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


@api.resource("/")
class Welcome(Resource):
    """Welcome resource"""

    def get(self):
        """CleanAir API welcome message"""
        return "Welcome to the CleanAir API developed by the Alan Turing Institute"


@api.resource('/users')
class Users(Resource):
    'User auth resources'
    @use_args({"username": fields.String(required=True), "password": fields.String(required=True)})
    def post(self, args):
        """Check if a user exists and if not add them and their hashed password to the database"""
        session = db_session()
        username = args['username']
        password = args['password']
        if check_user_exists(session, username=username).first() is not None:
            abort(400, message="username already exists")  # existing user
        user = create_user(session, username, password)

        return {'username': user.username}, 201


@api.resource("/point")
class Point(Resource):
    "Point resource"

    @use_args({"lat": fields.Float(required=True), "lon": fields.Float(required=True)})
    def get(self, args):
        """CleanAir API Point request"""
        session = db_session()
        points_forecast = get_point_forecast(
            session, args["lon"], args["lat"], output_type="query"
        )

        return results.dump(points_forecast)


@api.resource("/points")
class Points(Resource):
    "Points resource"

    @use_args(
        {
            "xmin": fields.Float(required=True),
            "ymin": fields.Float(required=True),
            "xmax": fields.Float(required=True),
            "ymax": fields.Float(required=True),
        }
    )
    def get(self, args):
        """CleanAir API Points request
           Get forecast for all points within a bounding box"""
        session = db_session()

        all_points = get_all_forecasts(
            session, args["xmin"], args["ymin"], args["xmax"], args["ymax"]
        )

        return results.dump(all_points)


@api.resource("/allpoints")
class AllPoints(Resource):
    "Points resource"

    @use_args(
        {
            "xmin": fields.Float(),
            "ymin": fields.Float(),
            "xmax": fields.Float(),
            "ymax": fields.Float(),
        }
    )
    def get(self, args):
        """CleanAir API Points request
           Get entire forecast for all points"""
        session = db_session()

        all_points = get_all_forecasts(session)

        return results.dump(all_points)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
