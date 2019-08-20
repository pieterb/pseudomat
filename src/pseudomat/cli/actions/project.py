import logging
import sys
import time
import typing as T

from jwcrypto import jwk, jws, jwt
import requests
from sqlalchemy.exc import IntegrityError

from ... import common
from .. import database, globals

_logger = logging.getLogger(__name__)

DEFAULT_PROJECT = 'default_project'


def create_local_project(iss: str, sub: str) -> database.Project:
    """
    Returns:
        A stored invite object.
    """
    sub = sub.strip(' ')
    project_id = common.fingerprint(sub)

    iat = int(time.time())

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
        'jti': project_id
    }
    default_claims = {
        'iss': iss,
        'sub': sub,
        'iat': iat
    }
    t = jwt.JWT(
        claims=claims,
        default_claims=default_claims,
        header={
            'alg': 'EdDSA',
            'typ': 'project'
        }
    )
    t.make_signed_token(sigkey)
    t = t.serialize()

    project = database.Project(
        jti=project_id,
        sub=sub,
        iss=iss,
        iat=iat,
        psig=psig,
        penc=penc,
        ssig=ssig,
        senc=senc,
        jws=t
    )
    try:
        database.add_project(project)
    except IntegrityError:
        sys.exit("A project with that name already exists.")

    return project


def create_remote_project(project: database.Project):
    # The next line is deliberately not in a try-except block. It’s no problem
    # to propagate this error all the way up.
    r = requests.put(
        url=globals.SERVER_URL / project.jti,
        headers={'Content-Type': 'application/jose'},
        data=project.jws,
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


def get_current_project(args=None, required=True) -> T.Optional[database.Project]:
    if args is not None and 'project' in args and args.project is not None:
        retval = database.get_project(sub=args.project)
        if retval is None:
            sys.exit("Project '%s' not found." % args.project)
    else:
        project_id = database.get_config(DEFAULT_PROJECT)
        if project_id is None:
            if required:
                sys.exit("No default project. Specify a project with --project.")
            else:
                return None
        retval = database.get_project(jti=project_id)
        assert retval is not None
    return retval


def set_default_project_id(project_id: T.Optional[str]):
    database.set_config(DEFAULT_PROJECT, project_id)


def list_projects(_args):
    projects = database.get_projects()
    default_project = get_current_project(required=False)
    for project in projects:
        line = 'M' if project.ssig is None else 'O'
        if default_project is not None and project.jti == default_project.jti:
            line += '*'
        else:
            line += ' '
        line += ': <%s> %s' % (project.iss, project.sub)
        print(line)


def delete_local_project(project):
    return database.delete_project(project)


def delete_remote_project(project: database.Project):
    payload = common.fingerprint({
        'method': 'DELETE',
        'path': '/' + project.jti
    })
    assert project.ssig is not None, "You’re not the owner of project '%s'." % project.sub
    sigkey = jwk.JWK.from_json(project.ssig)
    token = jws.JWS(payload=payload)
    token.add_signature(sigkey, protected={'alg': 'EdDSA'})
    token = token.serialize(compact=True)
    # The next line is deliberately not in a try-except block. It’s no problem
    # to propagate this error all the way up.
    r = requests.delete(
        url=globals.SERVER_URL / project.jti,
        headers={'Authorization': 'Bearer ' + token},
        allow_redirects=False
    )
    if r.status_code == 404:
        return
    if r.status_code in range(400, 500):
        sys.exit("%s: %s" % (r.reason, r.text))
    if r.status_code in range(500, 600):
        sys.exit("Server side error:\n%s: %s" % (r.reason, r.text))
    if r.status_code not in range(200, 300):
        sys.exit("Server returned unexpected response:\n%s: %s" % (r.reason, r.text))
    if r.status_code != 204:
        _logger.info("%s: %s" % (r.reason, r.text))
