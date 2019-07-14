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
    parser.add_argument('--no-log', action='store_true', dest='nolog')
    subparsers = parser.add_subparsers(
        title='Available commands',
        description=textwrap.dedent("""\
            project create
        """),
        dest='command',
        help="Run `%(prog)s COMMAND --help` for details.",
        metavar='COMMAND'
    )

    # PROJECT
    # =======
    project = subparsers.add_parser('project')
    project_subparsers = project.add_subparsers(
        title='Available subcommands',
        description=textwrap.dedent("""\
            create
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
            Create a new project, and register the project with the Pseudomat service.

            Idempotent: yes

            Output: the project ID of the created project
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

    retval = parser.parse_args()
    if retval.command is None:
        parser.print_help()
        parser.exit()
    if retval.subcommand is None:
        subparser = subparsers.choices[retval.command]
        subparser.print_help()
        subparser.exit()
    return retval


if __name__ == '__main__':
    print(repr(main()))
