"""Test we can execute queries in parallel"""
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from cleanair.databases import DBReader


@pytest.fixture()
def example_db_function(secretfile, connection):
    def f():

        reader = DBReader(secretfile=secretfile, connection=connection)

        session_ids = []
        for i in range(10):

            with reader.dbcnxn.open_session(threadsafe=True) as session:

                session_ids.append(id(session))

        return session_ids

    return f


def test_threadpool(example_db_function):
    "Check we get the same session within a thread"
    with ThreadPoolExecutor(max_workers=4) as executor:
        a = executor.submit(example_db_function)
        b = executor.submit(example_db_function)

        output_a = set(a.result())
        output_b = set(b.result())

        assert len(output_a) == 1
        assert len(output_b) == 1

        print(list(output_a)[0] != list(output_b)[0])
