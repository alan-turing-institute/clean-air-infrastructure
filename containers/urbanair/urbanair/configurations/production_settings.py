"""Production configuration environment variables"""
from werkzeug.security import generate_password_hash

DATABASE_SECRETFILE = "db_secrets.json"
SWAGGER_TEMPLATE = {
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