from flask import Flask
from flask_restful import Resource, Api
import numpy as np
import datetime

app = Flask(__name__)
api = Api(app)


PRED_DATA = [{'lat': np.random.rand(1) , 'lon': np.random.rand(1), 'datetime': datetime.datetime.now(), 'value': np.random.rand(1), 'var': np.random.rand(1)} for i in range(272451)]

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