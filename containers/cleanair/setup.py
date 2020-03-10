"""CleanAir module setup script"""
import setuptools

setuptools.setup(
    name="cleanair",
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
    install_requires=[
        'boto3==1.10.37',
        'colorlog==4.0.2',
        'geoalchemy2==0.6.3',
        'geopandas==0.6.2',
        'holidays==0.9.8',
        'matplotlib==3.1.2',
        'numpy==1.17.4',
        'pandas==0.25.3',
        'python-dateutil==2.8.1',
        'pytz==2019.3',
        'psycopg2-binary==2.8.4',
        'requests==2.22.0',
        'scipy==1.4.1',
        'sqlalchemy==1.3.11',
        'termcolor==1.1.0',
        'uuid==1.30',
      ],
    extras_require={
        'traffic': ['pystan==2.19.1.1', 'fbprophet==0.4', 'pathos==0.2.5'],
        'models': ['gpflow==1.5.1', 'tensorflow==1.15.0', 'scikit-learn==0.22.1'],
        'dashboard': ['dash-bootstrap-components==0.8.2', 'dash==1.8.0',]
    },
    python_requires=">=3.7",
)
