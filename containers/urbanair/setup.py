"""Urbanair API setup script"""
import setuptools

setuptools.setup(
    name="urbanair",
    setup_requires=["setuptools_scm"],
    use_scm_version={
        "root": "../..",
        "relative_to": __file__,
        "fallback_version": "0.2.7",
    },
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
        "fastapi[all]==0.78.0 ",
        "cachetools==5.2.0",
        "geojson==2.5.0",
        "sentry_sdk==1.5.12",
    ],
    python_requires=">=3.8",
)
