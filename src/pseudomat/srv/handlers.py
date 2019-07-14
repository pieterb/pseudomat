import logging

from aiohttp import web

from pseudomat import common

from . import database

_logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


@routes.get('/')
async def _get_root(_request: web.Request) -> web.Response:
    return web.Response(text="Hello, world")


@routes.post('/')
async def _post_root(request: web.Request) -> web.Response:
    if request.content_length is None:
        raise web.HTTPLengthRequired()
    if request.content_length > 65535:
        raise web.HTTPRequestEntityTooLarge(
            actual_size=request.content_length, max_size=65535
        )
    if request.content_type != 'application/jose':
        raise web.HTTPUnsupportedMediaType(
            text="Use application/jose instead of %s" % request.content_type
        )
    body = await request.text()
    jws_info = common.validate_project_jws(body)
    # return {
    #     'project_id': jti,
    #     'email': email,
    #     'name': name,
    #     'sig_key': uses['sig'][0],
    #     'enc_key': uses['enc'][0]
    # }

    await database.create_project(
        request,
        jws_info['project_id'],
        body,
        jws_info['sig_key'],
        jws_info['enc_key']
    )

    _logger.warning("Can’t send email yet.")
    return web.HTTPCreated(
        headers={
            'Location': str(request.rel_url / jws_info['project_id'])
        }
    )
