from flask import Flask
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import datetime
from cleanair.mixins import DBConnectionMixin
import logging
from cleanair.loggers import get_log_level

app = Flask(__name__)
api = Api(app)
db = SQLAlchemy(app)

logging.basicConfig(level=get_log_level(0))
DB_CONNECTION_INFO = DBConnectionMixin(
    "/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets.json"
)
print(DB_CONNECTION_INFO.connection_string)


PRED_DATA = [
    {
        "lat": np.random.rand(),
        "lon": np.random.rand(),
        "datetime": datetime.datetime.now().strftime("%Y-%M-%dT%H:%M:%S"),
        "value": np.random.rand(),
        "var": np.random.rand(),
    }
    for i in range(272451)
]


@api.resource("/")
class Welcome(Resource):
    def get(self):

        return "Welcome to the CleanAir API"


@api.resource("/forecast")
class Forecast(Resource):
    def get(self):

        return PRED_DATA


# api.add_resource(HelloWorld, '/')


if __name__ == "__main__":
    app.run(host="0.0.0.0")
