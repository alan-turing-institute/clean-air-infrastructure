"""Cleanair API"""

import os
from flask import Flask, jsonify
from . import db
from . import exceptions
from .blueprints import scoot_bp, index_bp


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URI="db_secrets.json",
    )

    # Create DB session object
    with app.app_context():
        db.init_app(app)

    # Register blueprints
    app.register_blueprint(index_bp)
    app.register_blueprint(scoot_bp, url_prefix='/api/v1/scoot/')

    # Configure exceptions
    exceptions.error_handler(app)

    return app


if __name__ == '__main__':

    app = create_app()
    print(app.config)
