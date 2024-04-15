"""CleanAir module setup script"""

from setuptools import setup, find_packages

# sorted by surname
AUTHORS = {
    "Sueda Ciftci": "sueda.ciftci@warwick.ac.uk",
    "Oscar Giles": "ogiles@turing.ac.uk",
    "Ollie Hamelijnck": "ohamelijnck@turing.ac.uk",
    "Patrick O'Hara": "patrick.h.o-hara@warwick.ac.uk",
    "James Robinson": "jrobinson@turing.ac.uk",
}
NAME = "cleanair_data"
URL = "https://github.com/alan-turing-institute/clean-air-infrastructure"
VERSION = "0.1.0"
CLASSIFIERS = [
    "Programming Language :: Python :: 3.11.7",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
DESCRIPTION = "Clean Air Data Module"

# Dependencies
INSTALL_REQUIRES = [
    "boto3==1.26.149",
    "botocore==1.29.149",
    "cdsapi==0.6.1",
    "cfgrib==0.9.10.4",
    "cryptography==40.0.2",
    "colorlog==6.7.0",
    "geoAlchemy2==0.14.2",
    "gitpython==3.1.31",
    "numpy==1.24.3",
    "packaging==23.1",
    "pathos==0.3.0",
    "pandas==2.1.0",
    "python-dateutil==2.8.2",
    "pytz==2023.3",
    "psycopg2-binary==2.9.7",
    "requests==2.31.0",
    "sqlalchemy==1.4.50",
    "sqlalchemy-utils==0.37.8",
    "shapely==2.0.1",
    "termcolor==2.3.0",
]
EXTRAS_REQUIRE = require = {
    "traffic": [
        "pystan==3.7.0",
        "fbprophet==0.7.1",
    ],
}
SETUP_REQUIRES = ["setuptools_scm"]

setup(
    name=NAME,
    version=VERSION,
    author=", ".join(AUTHORS.keys()),
    author_email=", ".join(AUTHORS.values()),
    description=DESCRIPTION,
    url=URL,
    install_requires=INSTALL_REQUIRES,
    packages=find_packages(),
    classifiers=CLASSIFIERS,
    setup_requires=SETUP_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    scripts=["cli/urbanair_db"],
)
