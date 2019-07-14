"""

We don’t raise custom Exceptions in case of config or project directory
corruption.  Instead, we do everything we can to prevent corruption.  If
corruption still occurs, the customer will see the (`OSError`?) exception on
stderr, and can post the stack trace from the log file on the forum.

"""

import pathlib
import sys

DEFAULT_PROJECT = 'default_project'
PROJECT_JWKS = 'project.jwks'
PROJECT_JWS = 'project.jws'


def config_dir() -> pathlib.Path:
    if sys.platform == 'linux':
        retval = pathlib.Path.home() / '.config' / 'pseudomat'
        retval.mkdir(parents=True, exist_ok=True)

    elif sys.platform == 'darwin':
        retval = pathlib.Path.home() / 'Library' / 'Application Support' / 'pseudomat'
        retval.mkdir(parents=True, exist_ok=True)

    else:
        sys.exit("Platform '%s' is not supported yet" % sys.platform)

    return retval


def project_dir(project_id: str) -> pathlib.Path:
    retval = config_dir() / project_id
    retval.mkdir(exist_ok=True)
    return retval


def project_file(project_id: str) -> pathlib.Path:
    return project_dir(project_id) / PROJECT_JWS


def project_keys(project_id: str) -> pathlib.Path:
    return project_dir(project_id) / PROJECT_JWKS


def set_default_project(project_id):
    symlink = config_dir() / DEFAULT_PROJECT
    try:
        symlink.unlink()
    except FileNotFoundError:
        pass
    symlink.symlink_to(project_id, target_is_directory=True)
