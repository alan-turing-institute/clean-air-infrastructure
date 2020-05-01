"""Cleanair API"""

import os
from flask import Flask
from flasgger import Swagger, APISpec
from . import db
from . import exceptions
from .blueprints import scoot_bp, index_bp


def create_app():

    # create and configure the app
    app = Flask(__name__)

    if app.config["ENV"] == "production":
        app.config.from_object("urbanair.configurations.production_settings")
    else:
        app.config.from_object("urbanair.configurations.development_settings")
        app.config["DATABASE_URI"] = os.environ.get("DATABASE_URI")
        if not app.config["DATABASE_URI"]:
            raise ValueError(
                "DATABASE_URI env variable must be set in development mode"
            )

    # Create DB session object
    with app.app_context():
        db.init_app(app)

    swagger = Swagger(app, template=app.config["SWAGGER_TEMPLATE"])

    # Register blueprints
    app.register_blueprint(index_bp)
    # app.register_blueprint(scoot_bp, url_prefix="/api/v1/scoot/")

    # Configure exceptions
    exceptions.error_handler(app)

    return app


__all__ = ["create_app"]

if __name__ == "__main__":

    app = create_app()
