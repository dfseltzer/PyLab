HELP_TEXT = """
Simple command line interface for adding scpi commands.

Commands
add COMMAND [FILE]: Add a command. Two arguments, COMMAND and optional FILE to add to.
"""

import argparse

GENERIC_ERROR_RETURN = 1

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pylab-inst",
        description="Simple command line interface for PyLab instrument control.",
        epilog=HELP_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )


    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    from ..communication import ConnectionTypes

    if not ConnectionTypes.is_known(args.conn_type):
        print(f"Unknown connection type specified ({args.conn_type}) - exiting.") 

    # Dispatch to the handler function for the chosen subcommand
    return args.func(args) or 0
