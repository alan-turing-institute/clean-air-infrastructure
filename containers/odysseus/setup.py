"""CleanAir Traffic module setup script"""
import setuptools

setuptools.setup(
    name="odysseus",
    version="0.0.1",
    author="Oscar Giles, James Robinson, Patrick O'Hara, Ollie Hamelijnck",
    author_email="ogiles@turing.ac.uk, jrobinson@turing.ac.uk, pohara@turing.ac.uk, ohamelijnck@turing.ac.uk",
    description="The Odysseus project for London's busyness.",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "astropy>=4.0.1",
        "cleanair>=0.0.1",
        "cloudpickle==1.4.1",  # NOTE https://github.com/tensorflow/probability/issues/991
        "gpflow>=2.1.3",
        "shapely>=1.7.0",
        "tensorflow>=2.3.0",
    ],
    python_requires=">=3.7",
    scripts=["cli/odysseus"],
)
