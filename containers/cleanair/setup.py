"""CleanAir module setup script"""
import setuptools

# sorted by surname
AUTHORS = {
    "Oscar Giles": "ogiles@turing.ac.uk",
    "Ollie Hamelijnck": "ohamelijnck@turing.ac.uk",
    "Patrick O'Hara": "patrick.h.o-hara@warwick.ac.uk",
    "James Robinson": "jrobinson@turing.ac.uk",
}

setuptools.setup(
    name="cleanair",
    author=", ".join(AUTHORS.keys()),
    author_email=", ".join(AUTHORS.values()),
    description="CleanAir",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "azure-cli==2.37.0",
        "azure-identity==1.10.0",
        "azure-storage-blob==12.12.0",
        "azure-mgmt-storage==20.0.0",
        "azure-mgmt-subscription==3.0.0",
        "boto3==1.24.0",
        "cdsapi==0.5.1",
        "cfgrib==0.9.10.1",
        "colorlog==6.6.0",
        "geoalchemy2==0.11.1",
        "gitpython==3.1.27",
        "holidays==0.13",
        "numpy==1.22.4",
        "packaging>=21.3",
        "pathos==0.2.9",
        "pandas==1.4.2",
        "pydantic==1.9.01"
        "pyeccodes==0.1.1",
        "python-dateutil==2.8.2",
        "pytz==2022.1",
        "pyyaml==6",
        "pycopg-binary==3.0.14 ",
        "requests==2.27.1",
        "scipy==1.8.1",
        "sqlalchemy==1.4.37",
        "sqlalchemy-utils==0.38.2",
        "scikit-learn==1.1.1",
        "shapely==1.8.2",
        "tabulate==0.8.9",
        "termcolor==1.1.0",
        "typer==0.4.1",
        "uuid==1.30",
        "xarray==2022.3.0",
        "orjson==3.6.8",
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
    python_requires=">=3.8",
    scripts=["cli/urbanair"],
)
