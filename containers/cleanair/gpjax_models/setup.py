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
    "jax==0.4.25",
    "jaxlib==0.4.27",
    "numpy==1.26.4",
    "pandas==2.2.2",
    "pydantic==1.10.12",
    "scikit-learn==1.5.1",
    "scipy==1.11.2",
    "tinygp==0.3.0",
    "tensorflow-probability==0.23.0",
    "nptyping==2.5.0",
    "matplotlib==3.9.1",
    "geopandas==1.0.1",
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
