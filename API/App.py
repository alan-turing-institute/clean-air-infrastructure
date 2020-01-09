from flask import Flask
from flask_restful import Resource, Api
import numpy as np
import datetime

app = Flask(__name__)
api = Api(app)


PRED_DATA = [{'lat': np.random.rand(), 'lon': np.random.rand(), 'datetime': datetime.datetime.now().strftime(
    "%Y-%M-%dT%H:%M:%S"), 'value': np.random.rand(), 'var': np.random.rand()} for i in range(272451)]


@api.resource('/')
class Welcome(Resource):
    def get(self):

        return 'Welcome to the CleanAir API'


@api.resource('/forecast')
class Forecast(Resource):
    def get(self):

        return PRED_DATA
# api.add_resource(HelloWorld, '/')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
