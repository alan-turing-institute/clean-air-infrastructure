"""CleanAir module setup script"""
import setuptools

# sorted by surname
AUTHORS = {
    "Sueda Ciftci": "sueda.ciftci@warwick.ac.uk",
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
        "gitpython==3.1.27 ",
    ],
    extras_require={
        "traffic": [
            "pystan==3.4.0",
            "fbprophet==0.7.1",
        ],
        "models": ["gpflow==1.5.1", "tensorflow==1.15.0"],
        "geo": ["geopandas>=0.10.0"],
    },
    setup_requires=["setuptools_scm"],
    use_scm_version={
        "root": "../..",
        "relative_to": __file__,
        "fallback_version": "0.2.13",
    },
    python_requires=">=3.8",
    scripts=["cli/urbanair"],
)
