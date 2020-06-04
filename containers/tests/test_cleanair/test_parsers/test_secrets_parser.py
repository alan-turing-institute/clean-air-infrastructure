"""Tests for the secret parser mixin"""
from argparse import ArgumentParser, ArgumentTypeError
import pytest
from cleanair.mixins import SecretFileParserMixin
from cleanair.databases import DBInteractor
from cleanair.parsers import SecretFileParser, VerbosityParser, SourceParser, DurationParser

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

def test_parser_mixins(secretfile):

    secret_parser = SecretFileParser(add_help=False)
    verbosity_parser = VerbosityParser(add_help=False)
    source_parser = SourceParser(sources = ['laqn', 'aqe'], add_help=False)
    duration_parser = DurationParser(ndays = 5, end  = 'tomorrow')

    myparser = ArgumentParser(parents=[secret_parser, verbosity_parser, source_parser])
    args = myparser.parse_args(["--secretfile", str(secretfile), '--secret-dict', 'password=sdfgs3', '-v'])

    print(args)

    assert args.sources == ['laqn', 'aqe']
    assert args.verbose == 1
    assert args.secretfile == str(secretfile)

@pytest.mark.parametrize("argument", ['lasthour', 'now', 'today', 'tomorrow', 'yesterday', '2020-01-01', '2020-01-01T00:00:00'])
def test_duration_parser_pass(argument):

    duration_parser = DurationParser()

    # Check valid arguments
    args = duration_parser.parse_args(['--upto', argument])
    assert args.upto == argument

@pytest.mark.parametrize("argument", ['lasthour2', '2020-01-40', '2020-01-01T25:00:00', '01/01/2020'])
def test_duration_parser_fails(capsys, argument):

    duration_parser = DurationParser()

    with pytest.raises(SystemExit):
        duration_parser.parse_args(['--upto', argument])

    stderr = capsys.readouterr().err
    assert 'is not a valid argument' in stderr