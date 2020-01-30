from flask import Flask
from flask_restful import Resource, Api
from flask_marshmallow import Marshmallow
import numpy as np
import datetime
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

logging.basicConfig(level=get_log_level(0))

DB_CONNECTION_INFO = DBConnectionMixin(
    "/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
)
engine = create_engine(DB_CONNECTION_INFO.connection_string, convert_unicode=True)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
DeferredReflection.prepare(engine)
Base.query = db_session.query_property()

app = Flask(__name__)
ma = Marshmallow(app)
api = Api(app)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


class Results(ma.Schema):
    class Meta:
        fields = [
            "lat",
            "lon",
            "point_id",
            "fit_time",
            "tag",
            "measurement_start_utc",
            "predict_mean",
            "predict_var",
        ]


results = Results(many=True)


@api.resource("/")
class Welcome(Resource):
    def get(self):

        return "Welcome to the CleanAir API"


@api.resource("/point")
class Point(Resource):
    @use_args({"lat": fields.Float(), "lon": fields.Float()})
    def get(self, args):
        # print(args)
        session = db_session()
        q = (
            session.query(
                func.ST_X(MetaPoint.location).label("lat"),
                func.ST_Y(MetaPoint.location).label("lon"),
                ModelResult.point_id,
                ModelResult.measurement_start_utc,
                ModelResult.predict_mean,
                ModelResult.predict_var,
            )
            .join(ModelResult)
            .limit(5)
            .all()
        )

        return results.dump(q)


@api.resource("/closest")
class Closest(Resource):
    @use_args({"lat": fields.Float(), "lon": fields.Float()})
    def get(self, args):

        session = db_session()

        # Find the closest point to the location
        closest_grid_point_sq = (
            session.query(
                func.ST_X(MetaPoint.location).label("lon"),
                func.ST_Y(MetaPoint.location).label("lat"),
                MetaPoint.id,
            )
            .filter(
                MetaPoint.source == "grid_100",
                func.ST_Intersects(
                    MetaPoint.location,
                    func.ST_Expand(
                        func.ST_SetSRID(
                            func.ST_MAKEPoint(args["lon"], args["lat"]), 4326
                        ),
                        0.001,
                    ),
                ),
            )
            .order_by(
                func.ST_Distance(
                    MetaPoint.location,
                    func.ST_SetSRID(func.ST_MAKEPoint(args["lon"], args["lat"]), 4326),
                )
            )
            .limit(1)
        ).subquery()

        print(session.query(closest_grid_point_sq).join(ModelResult).all())

        q = (
            session.query(
                func.ST_X(MetaPoint.location).label("lat"),
                func.ST_Y(MetaPoint.location).label("lon"),
                ModelResult.point_id,
                ModelResult.measurement_start_utc,
                ModelResult.predict_mean,
                ModelResult.predict_var,
            )
            .join(ModelResult)
            .limit(5)
            .all()
        )

        return results.dump(q)


# @api.resource("/fit-time")
# class FitTime(Resource):
#     def get(self):

#         session = db_session()
#         q = session.query(func.max(ModelResult.fit_start_time).label("fit_time")).all()

#         return results.dump(q)


# @api.resource("/forecast")
# class Forecast(Resource):
#     @use_args({"number": fields.Int()})
#     def get(self, args):
#         print(args)
#         session = db_session()
#         q = session.query(ModelResult).limit(args["number"]).all()

#         return results.dump(q)


# api.add_resource(HelloWorld, '/')


if __name__ == "__main__":
    app.run(host="0.0.0.0")
