import logging
import pathlib
import typing as T

from flask import Flask

_logger = logging.getLogger(__name__)


def create_app(test_config: T.Optional[dict] = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True, instance_path=pathlib.Path('./instance').absolute())

    # ensure the instance folder exists:
    instance_path = pathlib.Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        # SECRET_KEY='dev',
        DATABASE=instance_path / 'pseudomatd.sqlite',
    )

    if test_config is None:
        # load the instance config, when not testing
        app.config.from_pyfile('config.py', silent=False)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    from ..common.database import initialize_database, teardown_database
    initialize_database(app.config['DATABASE'])
    app.teardown_appcontext(teardown_database)

    from . import project
    app.register_blueprint(project.bp)

    return app
