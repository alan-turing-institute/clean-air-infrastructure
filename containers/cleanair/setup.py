"""CleanAir module setup script"""
import setuptools

setuptools.setup(
    name="cleanair",
    version="0.0.1",
    author="Oscar Giles, James Robinson, Patrick O'Hara, Ollie Hamelijnck",
    author_email="ogiles@turing.ac.uk, jrobinson@turing.ac.uk, pohara@turing.ac.uk, ohamelijnck@turing.ac.uk",
    description="CleanAir",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "boto3==1.10.37",
        "cdsapi==0.2.8",
        "cfgrib==0.9.8.1",
        "colorlog==4.0.2",
        "pyeccodes==0.1.1",
        "geoalchemy2==0.6.3",
        "gitpython==3.1.0",
        "holidays==0.9.8",
        "nptyping==1.2.0",
        "numpy==1.18.5",
        "pandas==1.0.5",
        "python-dateutil==2.8.1",
        "pytz==2019.3",
        "pyyaml==5.3.1",
        "psycopg2-binary==2.8.4",
        "requests==2.24.0",
        "scipy==1.4.1",
        "sqlalchemy==1.3.11",
        "sqlalchemy-utils==0.36.3",
        "scikit-learn==0.23.1",
        "tabulate==0.8.7",
        "termcolor==1.1.0",
        "uuid==1.30",
        "xarray==0.15.1",
    ],
    extras_require={
        "traffic": ["pystan==2.19.1.1", "fbprophet==0.4", "pathos==0.2.5"],
        "models": ["gpflow==1.5.1", "tensorflow==1.15.0"],
        "dashboard": [
            "dash-bootstrap-components==0.8.2",
            "dash==1.8.0",
            "plotly==4.4.1",
        ],
        "development": ["mypy", "sqlalchemy-stubs"]
    },
    python_requires=">=3.6",
)
