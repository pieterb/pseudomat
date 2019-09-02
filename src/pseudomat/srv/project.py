import logging

from flask import abort, Blueprint, request, url_for
import werkzeug.exceptions as exc

from pseudomat.common import database
from pseudomat import common

_logger = logging.getLogger(__name__)

bp = Blueprint('pseudomat', __name__)


@bp.route('/', methods=['GET'])
async def _get_root():
    return "Hello, world"


@bp.route('/', methods=['POST'])
async def _post_project():
    req = request
    if req.content_length is None:
        raise exc.LengthRequired()
    if req.content_length > 65535:
        raise exc.RequestEntityTooLarge(
            "%d bytes seems a bit large for a project jws." % req.content_length
        )
    if req.content_type != 'application/jose':
        raise exc.UnsupportedMediaType(
            "Use application/jose instead of %s." % req.content_type
        )
    try:
        body: str = req.get_data().decode('ascii')
    except UnicodeDecodeError:
        raise exc.BadRequest(
            "Request entity contains non-ascii characters."
        )
    payload = common.validate_project_jws(body)
    created = database.create_project(
        jti=payload['jti'],
        iss=payload['iss'],
        sub=payload['sub'],
        psig=common.json_dumps(payload['psig']),
        penc=common.json_dumps(payload['penc']),
        jws=body
    )
    # await sendgrid.send_confirmation_mail(
    #     request.app, payload['iss'], payload['sub'], project_id
    # )
    if not created:
        raise exc.Conflict(
            "Project with that name already exists."
        )
    created_url = url_for('_get_project', project_id=payload['jti'])
    return created_url, 201, {'Location': created_url}


@bp.route('/<project_id>', methods=['GET'])
async def _get_project(project_id):
    project = database.get_project(project_id)
    if project is None:
        raise exc.NotFound()
    return (
        project['jws'].encode('ascii'),
        200,
        {
            'Content-Type': 'application/jose'
        }
    )


@bp.route('/<project_id>', methods=['DELETE'])
async def _delete_project(project_id):
    pass
    # if not re.fullmatch(r'^[-\w]{32}$', project_id):
    #     raise web.HTTPNotFound(text="Illegal project id.")
    # project = await database.get_project(request.app, project_id)
    # if project is None:
    #     raise web.HTTPNotFound(text="Project not found.")
    # if 'Authorization' not in request.headers:
    #     raise web.HTTPUnauthorized()
    # authorization = re.fullmatch(r'^Bearer ([-\w.]+)$', request.headers['Authorization'])
    # if authorization is None:
    #     raise web.HTTPBadRequest(text="Illegal Authorization header format.")
    # token = authorization.group(1)
    # try:
    #     decoder = jws.JWS()
    #     decoder.deserialize(token, jwk.JWK.from_json(project['psig']), alg='EdDSA')
    # except jws.InvalidJWSObject:
    #     raise web.HTTPBadRequest(text="Couldn’t deserialize Bearer token.")
    # except jws.InvalidJWSSignature:
    #     raise web.HTTPUnauthorized(text="Invalid signature on Bearer token.")
    # if decoder.payload != common.fingerprint({'method': 'DELETE',
    #                                           'path': '/' + project_id}).encode('ascii'):
    #     raise web.HTTPUnauthorized(text="Invalid payload in Bearer token: '%s'" % decoder.payload)
    # await database.delete_project(request.app, project_id)
    # return web.HTTPNoContent()


@bp.route('/<project_id>/invites/<invite_id>', methods=['PUT'])
async def _put_invite(project_id, invite_id):
    pass
    # if request.content_length is None:
    #     raise web.HTTPLengthRequired()
    # if request.content_length > 65535:
    #     raise web.HTTPRequestEntityTooLarge(
    #         actual_size=request.content_length, max_size=65535
    #     )
    # if request.content_type != 'application/jose':
    #     raise web.HTTPUnsupportedMediaType(
    #         text="Use application/jose instead of %s" % request.content_type
    #     )
    #
    # project_id = request.match_info['project_id']
    # invite_id = request.match_info['invite_id']
    # if not re.fullmatch(r'^[-\w]{32}$', project_id) or not re.fullmatch(r'^[-\w]{32}$', invite_id):
    #     raise web.HTTPNotFound()
    #
    # project = await database.get_project(request.app, project_id)
    # if project is None:
    #     raise web.HTTPNotFound()
    #
    # from jwcrypto.jwk import JWK
    # project_key = JWK.from_json(project['psig'])
    # body = await request.text()
    # payload = common.validate_invite_jws(body, project_key)
    #
    # if project_id != payload['iss'] or invite_id != payload['jti']:
    #     raise web.HTTPForbidden(
    #         text="Claims 'iss' and 'jti' don’t correspond with request URI."
    #     )
    #
    # created = await database.create_invite(
    #     request.app,
    #     jti=payload['jti'],
    #     iss=payload['iss'],
    #     sub=payload['sub'],
    #     iat=payload['iat'],
    #     psig=common.json_dumps(payload['psig']),
    #     penc=common.json_dumps(payload['penc']),
    #     jws=body
    # )
    # if not created:
    #     return web.HTTPOk(text="Project already exists.")
    # return web.HTTPCreated()
