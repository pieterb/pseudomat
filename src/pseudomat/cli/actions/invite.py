import logging
import time
# import typing as T

from jwcrypto import jwk, jwt
import requests

from pseudomat import common

from ..globals import *
from .. import database

_logger = logging.getLogger(__name__)


def create_local_invite(project: database.Project, sub: str) -> database.Invite:
    """
    Returns:
        A stored project object.
    """
    sub = sub.strip(' ')
    iss = project.jti
    iat = int(time.time())
    jti = common.fingerprint([iss, sub])
    project_ssig = jwk.JWK.from_json(project.ssig)

    sigkey = jwk.JWK.generate(
        kty='OKP',
        crv='Ed448',
        use='sig'
    )
    psig = sigkey.export_public()
    ssig = sigkey.export()

    enckey = jwk.JWK.generate(
        kty='OKP',
        crv='X448',
        use='enc'

    )
    penc = enckey.export_public()
    senc = enckey.export()

    claims = {
        'psig': common.json_loads(psig),
        'penc': common.json_loads(penc),
        'jti': jti
    }
    default_claims = {
        'iss': iss,
        'sub': sub,
        'iat': iat
    }

    pjws = jwt.JWT(
        claims=claims,
        default_claims=default_claims,
        header={
            'alg': 'EdDSA',
            'typ': 'pinvite'
        }
    )
    pjws.make_signed_token(project_ssig)
    pjws = pjws.serialize()

    claims = {
        'ssig': common.json_loads(ssig),
        'senc': common.json_loads(senc),
        'jti': jti
    }
    sjws = jwt.JWT(
        claims=claims,
        default_claims=default_claims,
        header={
            'alg': 'EdDSA',
            'typ': 'sinvite'
        }
    )
    sjws.make_signed_token(project_ssig)
    sjws = sjws.serialize()

    invite = database.Invite(
        jti=jti,
        sub=sub,
        iss=iss,
        iat=iat,
        psig=psig,
        penc=penc,
        ssig=ssig,
        senc=senc,
        pjws=pjws,
        sjws=sjws
    )
    try:
        database.add_invite(invite)
    except database.IntegrityError:
        sys.exit("An invite with that name already exists.")

    return invite


def create_remote_invite(invite: database.Invite):
    # The next line is deliberately not in a try-except block. It’s no problem
    # to propagate this error all the way up.
    r = requests.put(
        url=SERVER_URL / invite.iss / 'invites' / invite.jti,
        headers={'Content-Type': 'application/jose'},
        data=invite.pjws,
        allow_redirects=False
    )
    if r.status_code in range(400, 500):
        sys.exit("%s: %s" % (r.reason, r.text))
    if r.status_code in range(500, 600):
        sys.exit("Server side error:\n%s: %s" % (r.reason, r.text))
    if r.status_code not in range(200, 300):
        sys.exit("Server returned unexpected response:\n%s: %s" % (r.reason, r.text))
    if r.status_code != 201:
        _logger.info("%s: %s" % (r.reason, r.text))


def delete_invite(invite: database.Invite):
    return database.delete_invite(invite)
