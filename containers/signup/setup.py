"""Sign-up Flask application"""
import setuptools

setuptools.setup(
    name="signup",
    version="0.0.1",
    author="David Perez-Suarez",
    author_email="d.perez-suarez@ucl.ac.uk",
    description="Sign-up frontend to provide access tokens",
    url="https://github.com/alan-turing-institute/clean-air-infrastructure",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "Flask>=1,<2",
        "werkzeug>=1,<2",
        "flask-session~=0.3.2",
        "requests>=2,<3",
        "msal>=0.6.1,<2",
        "python-jose",
    ],
    python_requires=">=3.8",
)
