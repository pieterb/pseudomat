import pathlib
import pytest

from pseudomat.srv import create_app


@pytest.fixture(scope="session")
def app():
    retval = create_app({
        'DATABASE': 'pseudomatd_test.sqlite'
    })
    yield retval
    pathlib.Path(retval.config['DATABASE']).unlink()


@pytest.fixture(scope="session")
def client(app):
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
