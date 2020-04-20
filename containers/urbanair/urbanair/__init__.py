"""Cleanair API"""


from flask import Flask
from flasgger import Swagger, APISpec
from . import db
from . import exceptions
from .blueprints import scoot_bp, index_bp


def create_app():

    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(DATABASE_URI="db_secrets.json")

    # Create DB session object
    with app.app_context():
        db.init_app(app)

    template = {
        "swagger": "2.0",
        "info": {
            "title": "UrbanAir API",
            "description": "API to access UrbanAir 48h air polution forecasts",
            "contact": {
                "responsibleOrganization": "Alan Turing Institute",
                "responsibleDeveloper": "Oscar T Giles",
                "email": "ogiles@turing.ac.uk",
                "url": "www.turing.ac.uk/research/research-projects/london-air-quality",
            },
            "termsOfService": "",
            "version": "0.0.1",
        },
        "host": "urbanair.turing.ac.uk",  # overrides localhost:5000
        "basePath": "/",  # base bash for blueprint registration
        "schemes": ["https"],
        "operationId": "getmyData",
    }

    swagger = Swagger(app, template=template)

    # Register blueprints
    app.register_blueprint(index_bp)
    app.register_blueprint(scoot_bp, url_prefix="/api/v1/scoot/")

    # Configure exceptions
    exceptions.error_handler(app)

    return app


__all__ = ["create_app"]

if __name__ == "__main__":

    app = create_app()
