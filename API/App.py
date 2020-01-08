from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

@api.resource('/')
class Welcome(Resource):
    def get(self):
        
        return 'Welcome to the CleanAir API'

@api.resource('/forecast')
class Forecast(Resource):
    def get(self):
        
        return [{'val1': 19}, {'val2': 25}]
# api.add_resource(HelloWorld, '/')

if __name__ == '__main__':
    app.run(host='0.0.0.0')