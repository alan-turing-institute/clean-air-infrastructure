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
NAME = "cleanair_types"
URL = "https://github.com/alan-turing-institute/clean-air-infrastructure"
VERSION = "0.1.0"
CLASSIFIERS = [
    "Programming Language :: Python :: 3.11.7",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]
DESCRIPTION = "Clean Air Type Module"

# Dependencies
INSTALL_REQUIRES = ["pydantic"]

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
)
