"""Test we can execute queries in parallel"""
from concurrent.futures import ThreadPoolExecutor
import pytest
from cleanair.databases import DBReader

# pylint: disable=C0103,W0621,W0613
@pytest.fixture()
def example_db_function(secretfile, connection):
    "Return a function"

    def f():
        "Example database function"
        reader = DBReader(secretfile=secretfile, connection=connection, threadsafe=True)

        session_ids = []
        for _ in range(10):
            with reader.dbcnxn.open_session() as session:
                session_ids.append(id(session))
        return session_ids

    return f


@pytest.mark.parametrize("i", [1, 2])
def test_threadpool(example_db_function, i):
    "Check we get the same session within a thread"
    with ThreadPoolExecutor(max_workers=4) as executor:
        a = executor.submit(example_db_function)
        output_a = set(a.result())

        assert len(output_a) == 1
