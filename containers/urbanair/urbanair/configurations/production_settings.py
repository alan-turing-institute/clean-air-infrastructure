"""Production configuration environment variables"""
from werkzeug.security import generate_password_hash
from .secret_readers import read_basic_auth_secret

DATABASE_SECRETFILE = "db_secrets.json"
DATABASE_SECRETFILE_JAMCAM = "db_secrets_jamcam.json"
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

# A development user and password
HTTP_BASIC_PASSWORD = 'x7WBcuRtrgK8255rPZcB'

USERS = {
    "ati": generate_password_hash(HTTP_BASIC_PASSWORD)
}