import asyncio
import logging
import sys
import typing as T

import uvloop
from aiohttp import web

from . import config, database, sendgrid
from .handlers import routes

_logger = logging.getLogger(__name__)


def context_initializer(
    context: T.AsyncContextManager,
    name: str
) -> T.Callable[[web.Application], T.Coroutine]:
    async def initialize(app):
        app[name] = await context.__aenter__()

        async def on_shutdown(_app):
            await context.__aexit__(None, None, None)
        app.on_shutdown.append(on_shutdown)
    return initialize


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
    app.on_startup.append(context_initializer(database.context(app), 'engine'))
    app.on_startup.append(context_initializer(sendgrid.context(app), 'sgsession'))
    web.run_app(app, port=app['config']['pseudomat']['bind_port'])


if __name__ == '__main__':
    sys.exit(main())
