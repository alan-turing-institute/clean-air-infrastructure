"""CleanAir module setup script"""
import setuptools

AUTHORS = {
    "Sueda Ciftci": "sueda.ciftci@warwick.ac.uk",
    "Oscar Giles": "ogiles@turing.ac.uk",
    "Ollie Hamelijnck": "ohamelijnck@turing.ac.uk",
    "Patrick O'Hara": "patrick.h.o-hara@warwick.ac.uk",
    "James Robinson": "jrobinson@turing.ac.uk",
}


setuptools.setup(
    name="cleanair",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "azure-identity==1.10.0",
        "azure-storage-blob==12.12.0",
        "azure-mgmt-subscription==3.0.0",
        "azure-cli-core==2.42.0",
        "azure-mgmt-storage==20.1.0",
        "azure-common==1.1.25",
        "boto3==1.26.14",
        "botocore==1.29.15",
        "cdsapi==0.2.8",
        "cfgrib==0.9.8.1",
        "cryptography==38.0.0",
        "colorlog==4.0.2",
        "geoalchemy2==0.6.3",
        "gitpython==3.1.0",
        "h5py==2.10.0",
        "holidays==0.9.8",
        "nptyping==1.2.0",
        "numpy==1.18.5",
        "packaging>=20.5",
        "pandas==1.0.5",
        "pydantic==1.6.1",
        "pyeccodes==0.1.1",
        "pyjwt==2.4.0",
        "pathos==0.2.5",
        "python-dateutil==2.8.1",
        "pytz==2019.3",
        "pyyaml==5.3.1",
        "pyopenssl==22.1.0",
        "psycopg2-binary==2.8.4",
        "requests==2.24.0",
        "scipy==1.4.1",
        "sqlalchemy==1.3.11",
        "sqlalchemy-utils==0.36.3",
        "scikit-learn==0.23.1",
        "shapely==1.7.1",
        "tabulate==0.8.7",
        "termcolor==1.1.0",
        "typer==0.7.0",
        "urllib3==1.25.4",
        "click==7.1.1",
        "uuid==1.30",
        "xarray==0.15.1",
        "orjson==3.6.0",
    ],
    extras_require={
        "traffic": [
            "pystan==2.19.1.1",
            "fbprophet==0.6",
        ],
        "models": ["gpflow==1.5.1", "tensorflow==1.15.0"],
    },
    setup_requires=["setuptools_scm"],
    use_scm_version={
        "root": "../..",
        "relative_to": __file__,
        "fallback_version": "0.0.3",
    },
    python_requires=">=3.7, <3.8",
    scripts=["cli/urbanair"],
)
