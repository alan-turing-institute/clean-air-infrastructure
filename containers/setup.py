"""CleanAir module setup script"""
import setuptools

setuptools.setup(
    name="cleanair",  # Replace with your own username
    version="0.0.1",
    author="Oscar Giles, James Robinson",
    author_email="ogiles@turing.ac.uk, jrobinson@turing.ac.uk",
    description="CleanAir",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
