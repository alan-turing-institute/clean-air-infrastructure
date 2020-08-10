All tests are written using the [pytest framework](https://docs.pytest.org/en/stable/) 

## Running tests

Tests should be written where possible before code is accepted into master. Contributing tests to existing code is highly desirable. Tests will also be run on travis (see the [travis configuration](.travis.yml)).

All tests can be found in the [`containers/tests/`](containers/tests) directory. We already ran some tests to check our local database was set up. 

To run the full test suite against the local database run

```bash
export DB_SECRET_FILE=$(pwd)/.secrets/.db_secrets_offline.json
```

```bash
pytest containers --secretfile $DB_SECRET_FILE
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