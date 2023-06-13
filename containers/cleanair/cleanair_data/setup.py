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
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
DESCRIPTION = "Clean Air Data Module"

# Dependencies
INSTALL_REQUIRES = [
    "azure-identity==1.13.0",
    "azure-storage-blob==12.16.0",
    "azure-mgmt-subscription==3.1.1",
    "azure-cli==2.49.0",
    "azure-cli-core==2.49.0",
    "azure-mgmt-storage==21.0.0",
    "azure-common==1.1.28",
    "boto3==1.26.149",
    "botocore==1.29.149",
    "cdsapi==0.6.1",
    "cfgrib==0.9.10.4",
    "cryptography==40.0.2",
    "colorlog==6.7.0",
    "geoalchemy2==0.13.3",
    "gitpython==3.1.31",
    "nptyping==2.5.0",
    "numpy==1.24.3",
    "packaging==23.1",
    "pathos==0.3.0",
    "pandas==2.0.2",
    "pydantic==1.10.9",
    "python-dateutil==2.8.2",
    "pytz==2023.3",
    "pyyaml==6.0",
    "psycopg2-binary==2.9.6",
    "requests==2.31.0",
    "scipy==1.10.1",
    "sqlalchemy<2.0.0",
    "sqlalchemy-utils",
    "shapely==2.0.1",
    "tabulate==0.9.0",
    "termcolor==2.3.0",
    "typer==0.9.0",
    "uuid==1.30",
    "uuid==1.30",
    "xarray==2023.5.0",
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
    scripts=["cli/urbanair"],
)
