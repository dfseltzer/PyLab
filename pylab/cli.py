HELP_TEXT = """
Simple command line interface for PyLab.

Universal Flags
-t [--type]:        Connection type.  Defaults to VISA

Commands
list:        List instruments found
identify A1:    Sends an identify command to the specified instrument.  Takes a single Address Argument A1 as a quote enclosed string.
write A1 C1:  Sends a command to the specified instrument as a write.  Both address "A1" and command "C1" are quote enclosed strings.
read A1 C1:  Sends a command to the specified instrument as a read.  Both address "A1" and command "C1" are quote enclosed strings.
"""

import argparse
import time

GENERIC_ERROR_RETURN = 1

def handle_list(args):
    """
    List known devices.
    """
    conn_type = args.conn_type
    print(f"Listing known equipment for connection type: {conn_type}")

    # list is different... so do for each...
    if conn_type == "VISA":
        try:
            from .communication.visa import ResourceManager
        except (ImportError, ModuleNotFoundError) as e:
            print(f"Unable to import required modules... are dependancies installed? Failed with {e}")
            return GENERIC_ERROR_RETURN
        dev_list = ResourceManager().list()
    else:
        print(f"CLI logic flow error... someone made a boo boo.")
        return GENERIC_ERROR_RETURN
    
    if not dev_list:
        print(f"No instruments found.")
        return GENERIC_ERROR_RETURN
    
    for idx, dev in enumerate(dev_list):
        print(f"[{idx+1:2d}] {dev}")
    print(dev_list)

def handle_identify(args):
    """
    Send a *IDN? query to the selected instrument
    """
    from .communication import getConnection

    print(f"Identifying {args.address}")
    conn_type = args.conn_type

    if conn_type != "VISA":
        print(f"Cannot identify for non VISA resources... exiting.")
        return GENERIC_ERROR_RETURN

    cnx = getConnection(conn_type)
    this_cnx = cnx("CLI-DEV", args.address)

    try:
        stat = this_cnx.open()
    except Exception as e:
        print(f"Failed to open connection with {e}")
        return GENERIC_ERROR_RETURN

    print(f"Connection open returned {stat}")
    if not stat:
        print(f"Connection not in useful state, exiting.")
        return GENERIC_ERROR_RETURN
    
    print(f"Sending *IDN?...")
    start = time.perf_counter()
    resp = this_cnx.query("*IDN?") # type: ignore
    end = time.perf_counter()
    print(f"Received response in {end - start:.6f}s.  Timeout is {this_cnx.timeout}s")
    print(f"*IDN? : {resp}")

def handle_write(args):
    """
    Send the specified command to the instrument, with the desired arguments.  Commands specified in this 
    way must exist in the instruments command_map
    """
    from .communication import getConnection

    print(f"Writing to {args.address}: {args.command}")
    conn_type = args.conn_type

    cnx = getConnection(conn_type)
    this_cnx = cnx("CLI-DEV", args.address)

    try:
        stat = this_cnx.open()
    except Exception as e:
        print(f"Failed to open connection with {e}")
        return GENERIC_ERROR_RETURN

    print(f"Connection open returned {stat}")
    if not stat:
        print(f"Connection not in useful state, exiting.")
        return GENERIC_ERROR_RETURN
    
    print(f"Sending {args.command}...")
    if this_cnx.write(args.command):
        print(f"Done. Seems OK...")
    else:
        print(f"Write failed!")

def handle_read(args):
    """
    Send the specified command to the instrument, with the desired arguments.  Commands specified in this 
    way must exist in the instruments command_map
    """
    """
    Send the specified command to the instrument, with the desired arguments.  Commands specified in this 
    way must exist in the instruments command_map
    """
    from .communication import getConnection

    print(f"Writing to {args.address}: {args.command}")
    conn_type = args.conn_type

    cnx = getConnection(conn_type)
    this_cnx = cnx("CLI-DEV", args.address)

    try:
        stat = this_cnx.open()
    except Exception as e:
        print(f"Failed to open connection with {e}")
        return GENERIC_ERROR_RETURN

    print(f"Connection open returned {stat}")
    if not stat:
        print(f"Connection not in useful state, exiting.")
        return GENERIC_ERROR_RETURN
    
    print(f"Sending {args.command}...")

    start = time.perf_counter()
    if this_cnx.write(args.command):
        print(f"Requested... seems OK...")
    else:
        print(f"Write failed!")
        return GENERIC_ERROR_RETURN
    print(f"Reading response...")
    resp = this_cnx.read() # type: ignore
    end = time.perf_counter()

    print(f"Received response in {end - start:.6f}s.  Timeout is {this_cnx.timeout}s")
    print(f"{args.command} : {resp}")
        
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pylab",
        description="Simple command line interface for PyLab.",
        epilog=HELP_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Universal flag
    parser.add_argument(
        "-t", "--type",
        dest="conn_type",
        default="VISA",
        help="Connection type. Defaults to VISA.",
    )

    # Subcommands
    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True,
    )

    # ---- list command ----
    list_parser = subparsers.add_parser(
        "list",
        help="List instruments found.",
    )
    list_parser.set_defaults(func=handle_list)

    # ---- identify command ----
    identify_parser = subparsers.add_parser(
        "identify",
        help='Send an identify command to the specified instrument.',
    )
    identify_parser.add_argument(
        "address",
        metavar="A1",
        help='Instrument address (quote-enclosed string).',
    )
    identify_parser.set_defaults(func=handle_identify)

    # ---- command write ----
    write_parser = subparsers.add_parser(
        "write",
        help='Send a command to the specified instrument.',
    )
    write_parser.add_argument(
        "address",
        metavar="A1",
        help='Instrument address (quote-enclosed string).',
    )
    write_parser.add_argument(
        "command",
        metavar="C1",
        help='Command to send (quote-enclosed string).',
    )
    write_parser.set_defaults(func=handle_write)

    # ---- command read ----
    read_parser = subparsers.add_parser(
        "read",
        help='Send a command to the specified instrument.',
    )
    read_parser.add_argument(
        "address",
        metavar="A1",
        help='Instrument address (quote-enclosed string).',
    )
    read_parser.add_argument(
        "command",
        metavar="C1",
        help='Command to send (quote-enclosed string).',
    )
    read_parser.set_defaults(func=handle_read)
    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    from .communication import ConnectionTypes

    if not ConnectionTypes.is_known(args.conn_type):
        print(f"Unknown connection type specified ({args.conn_type}) - exiting.") 

    # Dispatch to the handler function for the chosen subcommand
    return args.func(args) or 0
