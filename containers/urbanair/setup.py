<<<<<<< HEAD
"""Urbanair API setup script"""
import setuptools

setuptools.setup(
    name="urbanair",
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
        "cleanair",
        "odysseus",
        "flask",
        "flask-marshmallow",
        "flasgger",
        "webargs",
        "uwsgi",
    ],
    python_requires=">=3.7",
)
=======
"""Urbanair API setup script"""
import setuptools

setuptools.setup(
    name="urbanair",
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
        "cleanair",
        "odysseus",
        "flask",
        "flask-marshmallow",
        "flasgger",
        "webargs",
        "flask_httpauth",
        "uwsgi",
    ],
    python_requires=">=3.7",
)
>>>>>>> 566626e3b8beb34ade921a178a3b33a981c759c5
