"""CleanAir API Application"""
# pylint: skip-file
from flask import Flask, url_for, g
from flask_marshmallow import Marshmallow
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource, Api, abort
from webargs import fields
from webargs.flaskparser import use_args
from cleanair.mixins import DBConnectionMixin
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import DeferredReflection
from cleanair.databases.base import Base
from .queries import (
    get_point_forecast,
    get_all_forecasts,
    check_user_exists,
    create_user,
    get_user
)
from cleanair.databases.tables import User
import re


def check_password_valid(password):
    regex = re.compile('[@_!#$%^&*()<>?/\|}{~:1-9]')

    pass_len = len(password) < 6
    pass_upper = sum([1 for c in password if c.isupper()]) < 1
    pass_lower = sum([1 for c in password if c.islower()]) < 2
    special_character = (regex.search(password) == None)

    if pass_len or pass_upper or pass_lower or special_character:
        return False
    return True


# Initialise application
auth = HTTPBasicAuth()

app = Flask(__name__)
ma = Marshmallow(app)
api = Api(app)

# Configure session
DB_CONNECTION_INFO = DBConnectionMixin(
    "/Users/ogiles/Documents/project_repos/clean-air-infrastructure/terraform/.secrets/db_secrets-offline.json"


)
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

# Password verification
@auth.verify_password
def verify_password(username, password):
    session = db_session()
    user = get_user(session, username).first()
    g.user = user
    if not user or not user.verify_password(password):
        return False
    return True

# Serialization helpers


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


# Routes
@api.resource("/")
class Welcome(Resource):
    """Welcome resource"""

    def get(self):
        """CleanAir API welcome message"""
        return "Welcome to the CleanAir API developed by the Alan Turing Institute"


@api.resource("/register")
class Register(Resource):
    "Register to access the API"

    @use_args(
        {
            "username": fields.String(required=True),
            "password": fields.String(required=True),
            "email": fields.String(required=True),
        }
    )
    def post(self, args):
        """Check if a user exists and if not add them and their hashed password to the database"""
        session = db_session()
        username = args["username"]
        password = args["password"]
        email = args["email"]
        if check_user_exists(session, username=username).first() is not None:
            abort(400, message="username already exists")  # existing user
        if not check_password_valid(password):
            # existing user
            abort(400, message="Password must be 6 characters long, contain at least one captial and either a number or special character")
        user = create_user(session, username, password, email)

        return {"username": user.username}, 201


@api.resource("/token")
class Token(Resource):
    decorators = [auth.login_required]

    def get(self):
        token = g.user.generate_auth_token()
        if not token:
            abort(401, message="Token has not been approved")
        return token.decode("ascii")


@api.resource("/point")
class Point(Resource):
    "Point resource"
    decorators = [auth.login_required]
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
    decorators = [auth.login_required]

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
    decorators = [auth.login_required]

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
