import pytest
from pseudomat.common import database


@pytest.fixture(scope='module')
def db() -> database:
    database.initialize_database('pseudomat_tests.sqlite')
    return database
