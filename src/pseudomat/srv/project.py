import logging
import re

from flask import Blueprint, request, url_for

from ..common import database
from ..common.exceptions import *
from .. import common

_logger = logging.getLogger(__name__)

bp = Blueprint('pseudomat', __name__)


def _check_jose_upload() -> str:
    # language=rst
    """
    :raises HTTPResponse: with the following status codes:

        * ``411 Length Required``
        * ``413 Request Entity Too Large``
        * ``415 Unsupported Media Type`` if the ``Content-Type`` isn’t ``application/jose``
        * ``400 Bad Request`` if the request body contains non-ascii characters

    :returns: the request payload
    """
    req = request
    if req.content_length is None:
        raise HTTPResponse(411)  # Length Required
    if req.content_length > 65535:
        raise HTTPResponse(
            413,  # Request Entity Too Large
            "%d bytes seems a bit large for a jws." % req.content_length
        )
    if req.content_type != 'application/jose':
        raise HTTPResponse(
            415,  # Unsupported Media Type
            response="Use application/jose instead of %s." % req.content_type,
        )
    try:
        return req.get_data().decode('ascii')
    except UnicodeDecodeError:
        raise HTTPResponse(
            400,  # Bad Request
            "Request entity contains non-ascii characters."
        )


@bp.route('/', methods=['GET'])
def _get_root():
    raise HTTPMethodNotAllowed(['OPTIONS', 'POST'])


@bp.route('/', methods=['POST'])
def _post_project():
    body = _check_jose_upload()
    payload = common.validate_project_jws(body)
    created = database.create_project(
        jti=payload['jti'],
        iss=payload['iss'],
        sub=payload['sub'],
        psig=common.json_dumps(payload['psig']),
        penc=common.json_dumps(payload['penc']),
        jws=body
    )
    # sendgrid.send_confirmation_mail(
    #     request.app, payload['iss'], payload['sub'], project_id
    # )
    if not created:
        raise HTTPResponse(
            409,  # Conflict
            "A project with that name already exists."
        )
    created_url = url_for('pseudomat._get_project', project_id=payload['jti'])
    return HTTPLocation(201, created_url).response


@bp.route('/<project_id>', methods=['GET'])
def _get_project(project_id):
    project = database.get_project(project_id)
    if project is None:
        raise HTTPResponse(404)  # Not Found
    return (
        project['jws'].encode('ascii'),
        200,
        {
            'Content-Type': 'application/jose'
        }
    )


@bp.route('/<project_id>', methods=['DELETE'])
def _delete_project(project_id):
    if not re.fullmatch(r'^[-\w]{32}$', project_id):
        raise HTTPResponse(404, "Invalid project id.")  # Not Found
    if 'Authorization' not in request.headers:
        raise HTTPResponse(401)  # Unauthorized
    authorization = re.fullmatch(r'^Bearer ([-\w.]+)$', request.headers['Authorization'])
    if authorization is None:
        raise HTTPResponse(400, "Illegal Authorization header format.")
    token = authorization.group(1)
    project = database.get_project(project_id)
    if project is None:
        raise HTTPResponse(404, "Project not found.")  # Not Found
    from jwcrypto import jwk, jws
    try:
        decoder = jws.JWS()
        decoder.deserialize(token, jwk.JWK.from_json(project['psig']), alg='EdDSA')
    except jws.InvalidJWSObject:
        raise HTTPResponse(400, "Couldn’t deserialize Bearer token.")  # Bad Request
    except jws.InvalidJWSSignature:
        raise HTTPResponse(401, "Invalid signature on Bearer token.")  # Unauthorized
    if decoder.payload != common.fingerprint({'method': 'DELETE',
                                              'path': '/' + project_id}).encode('ascii'):
        raise HTTPResponse(401, "Invalid payload in Bearer token: '%s'" % decoder.payload)  # Unauthorized
    database.delete_project(project_id)
    return HTTPResponse(204).response


@bp.route('/<project_id>/invites/<invite_id>', methods=['PUT'])
def _put_invite(project_id, invite_id):
    if not re.fullmatch(r'^[-\w]{32}$', project_id) or not re.fullmatch(r'^[-\w]{32}$', invite_id):
        raise HTTPResponse(404)  # Not Found

    body = _check_jose_upload()

    project = database.get_project(project_id)
    if project is None:
        raise HTTPResponse(404)  # Not Found

    from jwcrypto.jwk import JWK
    project_key = JWK.from_json(project['psig'])
    payload = common.validate_invite_jws(body, project_key)

    if project_id != payload['iss'] or invite_id != payload['jti']:
        raise HTTPResponse(
            403,  # Forbidden
            "Claims 'iss' and 'jti' don’t correspond with request URI."
        )

    created = database.create_invite(
        jti=payload['jti'],
        iss=payload['iss'],
        sub=payload['sub'],
        iat=payload['iat'],
        psig=common.json_dumps(payload['psig']),
        penc=common.json_dumps(payload['penc']),
        jws=body
    )
    if not created:
        raise HTTPResponse(200, "Project already exists.")
    return HTTPLocation(201, request.url)
