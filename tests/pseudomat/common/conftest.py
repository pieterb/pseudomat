import pathlib

import pytest

from pseudomat.common import database


@pytest.fixture(scope='module')
def db() -> database:
    DBNAME = 'pseudomat_tests.sqlite'
    database.initialize_database(DBNAME)
    yield database
    pathlib.Path(DBNAME).unlink()
