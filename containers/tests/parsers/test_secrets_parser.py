"""Tests for the secret parser mixin"""
from argparse import ArgumentParser
from cleanair.mixins import SecretFileParserMixin
from cleanair.databases import DBInteractor


class ExampleConnectionParser(SecretFileParserMixin, ArgumentParser):
    """A simple parser to create a DBInteractor class"""


def test_secret_dict(secretfile):
    """Test that we can load yaml and read config file"""

    parser = ExampleConnectionParser()
    args = parser.parse_args(
        [
            "--secretfile",
            str(secretfile),
            "--secret-dict",
            "username=fakeuser",
            "port=6666",
        ]
    )

    db_interactor = DBInteractor(
        initialise_tables=False,
        secretfile=args.secretfile,
        secret_dict=args.secret_dict,
    )

    assert db_interactor.dbcnxn.connection_dict["username"] == "fakeuser"
    assert db_interactor.dbcnxn.connection_dict["port"] == 6666

def test_empty_secret_dict(secretfile):
    """Test that we can load yaml and read config file"""

    parser = ExampleConnectionParser()
    args = parser.parse_args(["--secretfile", str(secretfile)])

    assert args.secret_dict is None
