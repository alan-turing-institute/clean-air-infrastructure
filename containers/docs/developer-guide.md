# Developer guide

## Style guide

### Writing Documentation
Before being accepted into master all code should have well writen documentation. 

**Please use [Google Style Python Docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html)**

We would like to move towards adding [type hints](https://docs.python.org/3.7/library/typing.html) so you may optionally add types to your code. In which case you do not need to include types in your google style docstrings. 

Adding and updating existing documentation is highly encouraged.

### Gitmoji
We like [gitmoji](https://gitmoji.carloscuesta.me/) for an emoji guide to our commit messages. You might consider (entirly optional) to use the [gitmoji-cli](https://github.com/carloscuesta/gitmoji-cli) as a hook when writing commit messages. 

### Working on an issue

The general workflow for contributing to the project is to first choose and issue (or create one) to work on and assign yourself to the issues. 

You can find issues that need work on by searching by the `Needs assignment` label. If you decide to move onto something else or wonder what you've got yourself into please unassign yourself, leave a comment about why you dropped the issue (e.g. got bored, blocked by something etc) and re-add the `Needs assignment` label.

You are encouraged to open a pull request earlier rather than later (either a `draft pull request` or add `WIP` to the title) so others know what you are working on. 

How you label branches is optional, but we encourage using `iss_<issue-number>_<description_of_issue>` where `<issue-number>` is the github issue number and `<description_of_issue>` is a very short description of the issue. For example `iss_928_add_api_docs`.

## Running tests

Tests should be written where possible before code is accepted into master. Contributing tests to existing code is highly desirable. Tests will also be run on travis (see the [travis configuration](.travis.yml)).

All tests can be found in the [`containers/tests/`](containers/tests) directory. We already ran some tests to check our local database was set up. 

To run the full test suite against the local database run

```bash
SECRETS=$(pwd)/.secrets/.db_secrets_offline.json
```

```bash
pytest containers --secretfile $SECRETS
```

## Writing tests

The following shows an example test:

```python
def test_scoot_reading_empty(secretfile, connection):

    conn = DBWriter(
        secretfile=secretfile, initialise_tables=True, connection=connection
    )

    with conn.dbcnxn.open_session() as session:
        assert session.query(ScootReading).count() == 0
```

It uses the `DBWriter` class to  connect to the database. In general when interacting with a database we write a class which inherits from either `DBWriter` or `DBReader`. Both classes take a `secretfile` as an argument which provides database connection secrets.

**Critically, we also pass a special `connection` fixture when initialising any class that interacts with the database**. 

This fixture ensures that all interactions with the database take place within a `transaction`. At the end of the test the transaction is rolled back leaving the database in the same state it was in before the test was run, even if `commit` is called on the database. 
