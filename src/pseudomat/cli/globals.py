import pathlib
import sys
from yarl import URL

SERVER_URL = URL('http://localhost:5000/')


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
