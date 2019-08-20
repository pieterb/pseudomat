import logging
import sys

from . import actions


_logger = logging.getLogger(__name__)
PROJECT_JWS = 'project.jws'
PROJECT_JWKS = 'project.jwks'


def project_create(args):
    project = actions.project.create_local_project(args.email, args.name)
    try:
        actions.project.create_remote_project(project)
    except BaseException:
        actions.project.delete_local_project(project)
        raise
    if args.default:
        actions.project.set_default_project_id(project.jti)


def project_delete(args):
    current_project = actions.project.get_current_project(args)
    default_project = actions.project.get_current_project(required=False)
    actions.project.delete_remote_project(current_project)
    actions.project.delete_local_project(current_project)
    if default_project is not None and default_project.jti == current_project.jti:
        actions.project.set_default_project_id(None)


def project_info(_args):
    sys.exit("Sorry, not implemented yet.")


def project_list(args):
    actions.project.list_projects(args)


def invite_create(args):
    project = actions.project.get_current_project(args)
    invite = actions.invite.create_local_invite(project, args.name)
    try:
        actions.invite.create_remote_invite(invite)
    except BaseException:
        actions.invite.delete_invite(invite)
        raise
    print(invite.sjws)
