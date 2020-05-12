"""Cleanair API"""

import os
from flask import Flask
from flasgger import Swagger
from . import db
from . import exceptions
from .blueprints import scoot_bp, cams_bp, index_bp


def create_app():

    # create and configure the app
    app = Flask(__name__)

    if app.config["ENV"] == "production":
        app.config.from_object("urbanair.configurations.production_settings")
    else:
        app.config.from_object("urbanair.configurations.development_settings")
        app.config["DATABASE_URI"] = os.environ.get("DATABASE_URI")
        # app.config["DATABASE_URI_JAMCAM"] = os.environ.get("DATABASE_URI_JAMCAM")
        # if not app.config["DATABASE_URI"] or not app.config["DATABASE_URI_JAMCAM"]:
        #     raise ValueError(
        #         "DATABASE_URI and DATABASE_URI_JAMCAM env variable must be set in development mode"
        #     )

    # Create DB session object
    with app.app_context():
        db.init_app(app)

    swagger = Swagger(app, template=app.config["SWAGGER_TEMPLATE"])

    # Register blueprints
    app.register_blueprint(index_bp)
    # app.register_blueprint(scoot_bp, url_prefix="/api/v1/scoot/")
    app.register_blueprint(cams_bp, url_prefix="/api/v1/cams/")

    # Configure exceptions
    exceptions.error_handler(app)

    return app


__all__ = ["create_app"]

if __name__ == "__main__":

    app = create_app()
