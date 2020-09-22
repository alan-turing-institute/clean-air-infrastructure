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
        "fastapi[all]==0.60.1",
        "fastapi_contrib==0.2.8",
        "aiofiles",
        "cachetools",
        "geojson",
        "sentry_sdk",
    ],
    python_requires=">=3.7",
)
