<<<<<<< HEAD
"""Production configuration environement variables"""

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
    "host": "localhost:5000",  # overrides localhost:5000
    "basePath": "/",  # base bash for blueprint registration
    "schemes": ["http",],
    "operationId": "getmyData",
}
=======
"""Development configuration environement variables"""

from werkzeug.security import generate_password_hash

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
    "host": "localhost:5000",  # overrides localhost:5000
    "basePath": "/",  # base bash for blueprint registration
    "schemes": ["http",],
    "operationId": "getmyData",
}
>>>>>>> 566626e3b8beb34ade921a178a3b33a981c759c5
