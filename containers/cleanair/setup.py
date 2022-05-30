"""CleanAir module setup script"""
import setuptools

setuptools.setup(
    name="cleanair",
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
        "azure-cli==2.36.0",
        "azure-identity==1.10.0",
        "azure-storage-blob==12.12.0",
        "azure-mgmt-storage==20.0.0",
        "azure-mgmt-subscription==3.0.0",
        "boto3==1.10.37",
        "cdsapi==0.2.8",
        "cfgrib==0.9.8.1",
        "colorlog==4.0.2",
        "geoalchemy2==0.6.3",
        "gitpython==3.1.0",
        "h5py==2.10.0",
        "holidays==0.9.8",
        "nptyping==1.2.0",
        "numpy==1.22.4",
        "packaging>=20.5",
        "pathos==0.2.5",
        "pandas==1.4.2",
        "pathos==0.2.5",
        "pydantic==1.9.0",
        "pyeccodes==0.1.1",
        "python-dateutil==2.8.1",
        "pytz==2022.1",
        "pyyaml==5.3.1",
        "psycopg2-binary==2.8.4",
        "requests==2.27.1",
        "scipy==1.8.1",
        "sqlalchemy==1.4.36",
        "sqlalchemy-utils==0.38.2",
        "scikit-learn==1.1.1",
        "shapely==1.8.2",
        "tabulate==0.8.7",
        "termcolor==1.1.0",
        "typer==0.4.1",
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
        "fallback_version": "0.2.7",
    },
    python_requires=">=3.6",
    scripts=["cli/urbanair"],
)
