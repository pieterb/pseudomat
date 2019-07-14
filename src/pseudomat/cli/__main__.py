import logging
import sys

from . import argparse
from . import commands
from . import files

_logger = logging.getLogger(__name__)


def initialize_logging(nolog: bool, debug: bool):
    logger = logging.getLogger()
    loglevel = logging.DEBUG if debug else logging.INFO
    logger.setLevel(loglevel)

    if nolog:
        handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(files.config_dir() / 'cli.log')
    handler.setFormatter(
        logging.Formatter('%(asctime)s: %(levelname)-8s: %(name)s %(message)s')
    )
    logger.addHandler(handler)


def main():
    args = argparse.main()
    initialize_logging(args.nolog, args.debug)
    command = getattr(commands, f'{args.command}_{args.subcommand}')
    try:
        return command(args)
    except Exception as e:
        if args.nolog:
            raise
        _logger.exception(e)
        sys.exit("%s\nSee log file for details." % e)


if __name__ == '__main__':
    main()
