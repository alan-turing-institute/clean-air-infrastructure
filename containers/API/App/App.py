from flask import Flask
from flask_restful import Resource, Api
from flask_marshmallow import Marshmallow
from cleanair.mixins import DBConnectionMixin
import logging
from cleanair.loggers import get_log_level
from sqlalchemy import create_engine, func
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from sqlalchemy.ext.declarative import declarative_base
from cleanair.databases.base import Base
from cleanair.databases.tables import ModelResult, MetaPoint
from sqlalchemy.ext.serializer import loads, dumps
from webargs import fields
from webargs.flaskparser import use_args
from .queries import *
# Initialise application
app = Flask(__name__)
ma = Marshmallow(app)
api = Api(app)

# Configure session
DB_CONNECTION_INFO = DBConnectionMixin(
    "db_secrets.json"
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
    db_session.remove()


class Results(ma.Schema):
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
    def get(self):

        return "Welcome to the CleanAir API developed by the Alan Turing Institute"


@api.resource("/point")
class Point(Resource):
    @use_args({"lat": fields.Float(), "lon": fields.Float()})
    def get(self, args):

        session = db_session()
        points_forecast = get_point_forecast(session, args['lon'], args['lat'], output_type='query')

        return results.dump(points_forecast)


@api.resource("/points")
class Points(Resource):
    @use_args({"xmin": fields.Float(), "ymin": fields.Float(), 'xmax': fields.Float(), 'ymax': fields.Float()})
    def get(self, args):

        session = db_session()
        all_points = get_all_forecasts(session, args['xmin'], args['ymin'], args['xmax'], args['ymax'])

        return results.dump(all_points)


if __name__ == "__main__":
    app.run(host="0.0.0.0")
