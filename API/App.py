"""API for CleanAir predictions"""
import datetime
from flask import Flask
from flask_restful import Resource, Api
import numpy as np

FLASK_APP = Flask(__name__)
FLASK_API = Api(FLASK_APP)


@FLASK_API.resource("/")
class Welcome(Resource):
    """Class docstring"""
    name = "CleanAir API"
    def get(self):
        """Function docstring"""
        return f"Welcome to the {self.name}"


@FLASK_API.resource("/forecast")
class Forecast(Resource):
    """Class docstring"""

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

    def get(self):
        """Function docstring"""
        return self.PRED_DATA

# FLASK_API.add_resource(HelloWorld, '/')


if __name__ == "__main__":
    FLASK_APP.run(host="0.0.0.0")
