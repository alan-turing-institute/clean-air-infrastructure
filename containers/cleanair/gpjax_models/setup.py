"""CleanAir module setup script"""
from setuptools import setup, find_packages

# sorted by surname
AUTHORS = {
    "Sueda Ciftci": "sueda.ciftci@warwick.ac.uk",
    "Ollie Hamelijnck": "ohamelijnck@turing.ac.uk",
    "Patrick O'Hara": "patrick.h.o-hara@warwick.ac.uk",
}
NAME = "jax_models"
URL = "https://github.com/alan-turing-institute/clean-air-infrastructure"
VERSION = "0.1.0"
CLASSIFIERS = [
    "Programming Language :: Python :: 3.11.4",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
DESCRIPTION = "Jax Models Module"

# Dependencies
INSTALL_REQUIRES = [
    "azure-identity==1.13.0",
    "azure-storage-blob==12.16.0",
    "azure-mgmt-subscription==3.1.1",
    "azure-mgmt-resource",
    "azure-mgmt-storage",
    "azure-common==1.1.28",
    "jax",
    "numpy",
    "pandas==2.0.3",
    "pydantic==1.10.12",
    "scikit-learn",
    "scipy==1.11.1",
    "typer==0.9.0",
    "tensorflow-probability",
    "colorlog==6.7.0",
    "nptyping==2.5.0",
]
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
    scripts=["cli/urbanair_jax"],
)
