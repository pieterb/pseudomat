import argparse
import logging
import textwrap

_logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        prog='pseudomat',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-d', '--debug', action='store_true', dest='debug')
    subparsers = parser.add_subparsers(
        title='Available commands',
        description=textwrap.dedent("""\
            invite
            project
        """),
        dest='command',
        help="Run `%(prog)s COMMAND --help` for details.",
        metavar='COMMAND'
    )

    add_invite(subparsers)
    add_project(subparsers)

    retval = parser.parse_args()
    if retval.command is None:
        parser.print_help()
        parser.exit()
    if retval.subcommand is None:
        subparser = subparsers.choices[retval.command]
        subparser.print_help()
        subparser.exit()
    return retval


def add_invite(subparsers):
    invite = subparsers.add_parser(
        'invite',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    invite_subparsers = invite.add_subparsers(
        title='Available subcommands',
        description=textwrap.dedent("""\
            create
        """),
        dest='subcommand',
        help="Run `%(prog)s SUBCOMMAND --help` for details.",
        metavar='SUBCOMMAND'
    )

    # INVITE CREATE
    # -------------
    invite_create = invite_subparsers.add_parser(
        'create',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
Create a new invite, and register the invite with the Pseudomat service. This
command is idempotent.

Output: the invitation token you can send to the intended project member.
        """)
    )
    invite_create.add_argument(
        'name',
        help='The name of the party you wish to invite. This name will be visible to all project members.',
        action='store',
        metavar='invitee_name'
    )
    invite_create.add_argument(
        '-p', '--project',
        help="Name of the project to use, instead of the default project.",
        action='store',
        dest='project',
        metavar='project_name'
    )


def add_project(subparsers):
    project = subparsers.add_parser(
        'project',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    project_subparsers = project.add_subparsers(
        title='Available subcommands',
        description=textwrap.dedent("""\
            create
            delete
            info
            list
        """),
        dest='subcommand',
        help="Run `%(prog)s SUBCOMMAND --help` for details.",
        metavar='SUBCOMMAND'
    )

    # PROJECT CREATE
    # --------------
    project_create = project_subparsers.add_parser(
        'create',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""
            Create a new project, and register the project with the Pseudomat service. This
            command is idempotent.
        """)
    )
    project_create.add_argument(
        'email',
        help='The Pseudomat service will send project status updates to this address. The address will be visible to all future project members, to identify you as the project owner.',
        action='store',
        metavar='email_address'
    )
    project_create.add_argument(
        'name',
        help='The project name. It must be unique for the given email address.',
        action='store',
        metavar='project_name'
    )
    project_create.add_argument(
        '--no-default',
        help="Don’t set the newly created project as the default project.",
        action='store_false',
        dest='default'
    )

    # PROJECT DELETE
    # --------------
    project_delete = project_subparsers.add_parser(
        'delete',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Delete a project.
        """)
    )
    project_delete.add_argument(
        '-p', '--project',
        help='The name of the project you want to delete.',
        action='store',
        required=True,
        dest='project',
        metavar='project_name'
    )

    # PROJECT INFO
    # ------------
    project_info = project_subparsers.add_parser(
        'info',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Show available information about a project.
        """)
    )
    project_info.add_argument(
        '-p', '--project',
        help='The name of the project you want info about. If omitted, this command returns info about the default project.',
        action='store',
        dest='project',
        metavar='project_name'
    )

    # PROJECT LIST
    # --------------
    _project_list = project_subparsers.add_parser(
        'list',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            List all projects.

            Outputs one line per project, with the following formatting:
                'O'|'M' '*'? ':' <email_address> project_name

            The first character indicates if you are the owner of the project ('O') or just
            a project member ('M').

            The optional asterisk '*' indicates the current default project.
        """)
    )


if __name__ == '__main__':
    print(repr(main()))
