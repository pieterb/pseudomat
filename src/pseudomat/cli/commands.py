import logging
import sys

from . import actions, files


_logger = logging.getLogger(__name__)
PROJECT_JWS = 'project.jws'
PROJECT_JWKS = 'project.jwks'


def project_create(args):
    project_id = actions.create_local_project(args.email, args.name)
    if args.default:
        files.set_default_project(project_id)
    actions.create_remote_project(project_id)
    print(project_id)
