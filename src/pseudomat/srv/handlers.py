import logging
import re

from aiohttp import web

from jwcrypto import jwk, jws
from pseudomat import common

from . import database

_logger = logging.getLogger(__name__)
routes = web.RouteTableDef()


@routes.get('/')
async def _get_root(_request: web.Request) -> web.Response:
    return web.Response(text="Hello, world")


@routes.put('/{project_id}')
async def _put_project(request: web.Request) -> web.Response:
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
    payload = common.validate_project_jws(body)
    if request.match_info['project_id'] != payload['jti']:
        raise web.HTTPForbidden(
            text="Project ID (in path) is incorrect for this JWS."
        )

    created = await database.create_project(
        request.app,
        jti=payload['jti'],
        iss=payload['iss'],
        sub=payload['sub'],
        iat=payload['iat'],
        psig=common.json_dumps(payload['psig']),
        penc=common.json_dumps(payload['penc']),
        jws=body
    )
    # await sendgrid.send_confirmation_mail(
    #     request.app, payload['iss'], payload['sub'], project_id
    # )
    if not created:
        return web.HTTPOk(text="Project already exists.")
    return web.HTTPCreated()


@routes.delete('/{project_id}')
async def _delete_project(request: web.Request) -> web.Response:
    project_id = request.match_info['project_id']
    if not re.fullmatch(r'^[-\w]{32}$', project_id):
        raise web.HTTPNotFound(text="Illegal project id.")
    project = await database.get_project(request.app, project_id)
    if project is None:
        raise web.HTTPNotFound(text="Project not found.")
    if 'Authorization' not in request.headers:
        raise web.HTTPUnauthorized()
    authorization = re.fullmatch(r'^Bearer ([-\w.]+)$', request.headers['Authorization'])
    if authorization is None:
        raise web.HTTPBadRequest(text="Illegal Authorization header format.")
    token = authorization.group(1)
    try:
        decoder = jws.JWS()
        decoder.deserialize(token, jwk.JWK.from_json(project['psig']), alg='EdDSA')
    except jws.InvalidJWSObject:
        raise web.HTTPBadRequest(text="Couldn’t deserialize Bearer token.")
    except jws.InvalidJWSSignature:
        raise web.HTTPUnauthorized(text="Invalid signature on Bearer token.")
    if decoder.payload != common.fingerprint({'method': 'DELETE',
                                              'path': '/' + project_id}).encode('ascii'):
        raise web.HTTPUnauthorized(text="Invalid payload in Bearer token: '%s'" % decoder.payload)
    await database.delete_project(request.app, project_id)
    return web.HTTPNoContent()


@routes.put('/{project_id}/invites/{invite_id}')
async def _put_invite(request: web.Request) -> web.Response:
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

    project_id = request.match_info['project_id']
    invite_id = request.match_info['invite_id']
    if not re.fullmatch(r'^[-\w]{32}$', project_id) or not re.fullmatch(r'^[-\w]{32}$', invite_id):
        raise web.HTTPNotFound()

    project = await database.get_project(request.app, project_id)
    if project is None:
        raise web.HTTPNotFound()

    from jwcrypto.jwk import JWK
    project_key = JWK.from_json(project['psig'])
    body = await request.text()
    payload = common.validate_invite_jws(body, project_key)

    if project_id != payload['iss'] or invite_id != payload['jti']:
        raise web.HTTPForbidden(
            text="Claims 'iss' and 'jti' don’t correspond with request URI."
        )

    created = await database.create_invite(
        request.app,
        jti=payload['jti'],
        iss=payload['iss'],
        sub=payload['sub'],
        iat=payload['iat'],
        psig=common.json_dumps(payload['psig']),
        penc=common.json_dumps(payload['penc']),
        jws=body
    )
    if not created:
        return web.HTTPOk(text="Project already exists.")
    return web.HTTPCreated()
