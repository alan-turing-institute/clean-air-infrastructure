"""CleanAir Traffic module setup script"""
import setuptools

setuptools.setup(
    name="odysseus",
    version="0.0.1",
    author="Oscar Giles, James Robinson, Patrick O'Hara, Ollie Hamelijnck",
    author_email="ogiles@turing.ac.uk, jrobinson@turing.ac.uk, pohara@turing.ac.uk, ohamelijnck@turing.ac.uk",
    description="CleanAir Traffic module for CleanAir traffic modules",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "cleanair",
        "gpflow==2.0.0",
        "tensorflow==2.1.0",
        "tensorflow_probability==0.9",
    ],
    python_requires=">=3.7",
)
