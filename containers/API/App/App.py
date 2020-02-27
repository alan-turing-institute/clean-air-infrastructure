"""CleanAir API Application"""
# pylint: skip-file
from flask import Flask
from flask_restful import Resource, Api
from flask_marshmallow import Marshmallow
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base
from webargs import fields
from webargs.flaskparser import use_args
from .queries import get_point_forecast, get_all_forecasts

# Initialise application
app = Flask(__name__)
ma = Marshmallow(app)
api = Api(app)

# Configure session
DB_CONNECTION_INFO = DBConnectionMixin(
    "/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
)
engine = create_engine(DB_CONNECTION_INFO.connection_string, convert_unicode=True)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
DeferredReflection.prepare(engine)
Base.query = db_session.query_property()


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


@api.resource("/box")
class Box(Resource):
    "Box resource"

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
            session,
            args["xmin"],
            args["ymin"],
            args["xmax"],
            args["ymax"],
            output_type="query",
        )

        return results.dump(all_points)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
