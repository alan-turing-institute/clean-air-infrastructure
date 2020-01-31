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
DB_CONNECTION_INFO = DBConnectionMixin("db_secrets.json")
engine = create_engine(DB_CONNECTION_INFO.connection_string, convert_unicode=True)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
DeferredReflection.prepare(engine)
Base.query = db_session.query_property()

# Ensure sessions are closed by flask
@app.teardown_appcontext
def shutdown_session():
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

    def get():
        """CleanAir API welcome message"""
        return "Welcome to the CleanAir API developed by the Alan Turing Institute"


@api.resource("/point")
class Point(Resource):
    "Point resource"

    @use_args({"lat": fields.Float(), "lon": fields.Float()})
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
            "xmin": fields.Float(),
            "ymin": fields.Float(),
            "xmax": fields.Float(),
            "ymax": fields.Float(),
        }
    )
    def get(self, args):
        """CleanAir API Points request"""
        session = db_session()
        all_points = get_all_forecasts(
            session, args["xmin"], args["ymin"], args["xmax"], args["ymax"]
        )

        return results.dump(all_points)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
