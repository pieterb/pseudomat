import asyncio
import logging
import os.path
import sys

import swagger_parser
import uvloop
from aiohttp import web

from . import database, config
from .handlers import routes

_logger = logging.getLogger(__name__)


def main():
    # language=rst
    """The entry point of the authorization administration service.

    :returns int: the exit status of the process. See
        also the ``console_scripts`` in :file:`setup.py`.

    """
    # Set UVLoop as our default event loop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    app = web.Application()
    app['config'] = config.load()
    app['metadata'] = database.metadata()
    app.add_routes(routes)
    app.on_startup.append(database.initialize_app)
    web.run_app(
        app,
        port=app['config']['pseudomat']['bind_port']
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
