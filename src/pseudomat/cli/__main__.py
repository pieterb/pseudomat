import logging
import sys

from . import argparse

_logger = logging.getLogger(__name__)


def initialize_logging(debug: bool):
    logger = logging.getLogger('pseudomat')
    if debug:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter('%(levelname)-8s: %(module)s:%(lineno)d: %(message)s')
        )
        logger.addHandler(handler)
    else:
        logger.setLevel(logging.INFO)
        from . import globals
        filehandler = logging.FileHandler(globals.config_dir() / 'cli.log')
        filehandler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)-8s %(module)s:%(lineno)d: %(message)s')
        )
        logger.addHandler(filehandler)
        consolehandler = logging.StreamHandler()
        consolehandler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )
        logger.addHandler(consolehandler)
        logger.propagate = False
        logging.getLogger().addHandler(filehandler)


def initialize_database():
    import sqlalchemy as sa
    from ..common import database
    from . import globals
    engine = sa.create_engine(
        'sqlite:///' + str(globals.config_dir() / 'pseudomat.sqlite'),
        isolation_level='SERIALIZABLE'
    )
    database.set_engine(engine)


def main():
    args = argparse.main()
    initialize_logging(args.debug)
    initialize_database()
    from . import commands
    command = getattr(commands, f'{args.command}_{args.subcommand}')
    try:
        return command(args)
    except AssertionError as e:
        sys.exit(str(e))
    except Exception as e:
        if args.debug:
            raise
        logging.getLogger().exception(e)
        sys.exit("%s\nSee log file for details." % e)


if __name__ == '__main__':
    main()
