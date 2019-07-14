import json
import logging
import sys

from jwcrypto import jwk, jwt
import requests
from yarl import URL

from pseudomat import common

from . import files

_logger = logging.getLogger(__name__)

PROJECT_JWS = 'project.jws'
PROJECT_JWKS = 'project.jwks'
SERVER_URL = URL('http://localhost:8080/')


def create_local_project(email: str, name: str) -> str:
    """
    Returns:
        str: the project_id of the created project.
    """
    project_id = common.project_id(email, name)

    project_file = files.project_file(project_id)
    project_keys = files.project_keys(project_id)
    if project_file.exists():
        if project_keys.exists():
            return project_id
        else:
            sys.exit("Project already exists, and you’re not the owner.")

    signing_key = jwk.JWK.generate(
        kty='EC',
        crv='P-384',
        use='sig'

    )
    signing_key = common.with_kid(signing_key)

    encryption_key = jwk.JWK.generate(
        kty='EC',
        crv='P-384',
        use='enc'

    )
    encryption_key = common.with_kid(encryption_key)

    jwks = jwk.JWKSet()
    jwks['keys'].add(signing_key)
    jwks['keys'].add(encryption_key)

    # Lack of exception handling is deliberate: this should never fail.
    with project_keys.open(mode='xt', encoding='utf-8') as f:
        f.write(jwks.export(private_keys=True))

    claims = json.loads(jwks.export(private_keys=False))
    claims['jti'] = project_id

    default_claims = {
        'iss': email,
        'sub': name,
        'iat': None
    }
    t = jwt.JWT(
        claims=claims,
        default_claims=default_claims,
        header={
            'alg': 'ES384',
            'kid': signing_key.key_id
        }
    )
    t.make_signed_token(signing_key)

    # Lack of exception handling is deliberate: this should never fail.
    with project_file.open(mode='xt', encoding='utf-8') as f:
        f.write(t.serialize())

    return project_id


def create_remote_project(project_id):
    with files.project_file(project_id).open(mode='rt', encoding='utf-8') as fh:
        project_data = fh.read()
    # The next line is deliberately not in a try-except block. It’s no problem
    # to propagate this error all the way up.
    r = requests.post(
        url=SERVER_URL,
        headers={'Content-Type': 'application/jose'},
        data=project_data.encode('utf-8'),
        allow_redirects=False
    )
    if r.status_code == 412:  # HTTP 412: Precondition Failed
        sys.exit("Another project with the same e-mail address and name already exist on the server.")
    if r.status_code == 303:  # HTTP 303: See Other
        _logger.info(
            "The project was already registered with the Pseudomat service."
        )
    elif r.status_code != 201:  # HTTP 201: Created
        sys.exit("Server returned unexpected HTTP status code: %r" % r.status_code)
