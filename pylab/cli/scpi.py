HELP_TEXT = """
Simple command line interface for adding scpi commands.

Commands
add COMMAND [FILE]: Add a command. Two arguments, COMMAND and optional FILE to add to.
"""

import argparse
import pprint

from pylab.utilities import list_data_files
from pylab.utilities import load_data_file
from pylab.utilities import update_data_file


GENERIC_ERROR_RETURN = 1

SCPI_TYPES = (("bool", "True/False, 1/0, and ON/OFF.", lambda x: x in (True, "True", "TRUE", "on", "ON", 1, "1")), 
              ("int", "Integer or convertable to integer.", lambda x: int(x)),
              ("float", "Floating point numeric.", lambda x: float(x)), 
              ("str", "Strings.", lambda x: str(x)))

SCPI_TYPES_PROMPT = "\n".join(
        f"...... [{idx+1:2d}] {key} - {val}" for idx, (key,val, _) in enumerate(SCPI_TYPES)
    ) + f"\n...... [{len(SCPI_TYPES)+1:2d}] Abort and Exit"

# handlers
def handle_add(args):
    cmdname = args.command_name
    filename = args.file if args.file is not None else get_filename(indent=1)
    print(f"Adding to file {filename}")
    filedata = load_file(filename)

    if cmdname in filedata["commands"]:
        raise SystemExit(f"Command {cmdname} already exists in {filename}.  Update not implemented yet. Exiting.")
    
    print(f"Adding new command {cmdname} to file {filename}")
    cmddict = dict()

    has_set = get_response_yesno("Does this command support sets [Y/n]?",'y')
    if not has_set:
        cmddict["set"] = None
        set_format_accepted = True
    else:
        set_format_accepted = False
    while not set_format_accepted:
        cmddict["set"] = get_argument_list()
        print(f"Set formatting finished:\n{cmdname}['set']=", end="")
        pprint.pprint(cmddict["set"], indent=4)
        set_format_accepted = get_response_yesno(f"Accept format [Y] or re-do[n]?", default='y')
    
    has_query = get_response_yesno("Does this command support queries [Y/n]?",'y')
    if not has_query:
        cmddict["query"] = None
        cmddict["response"] = None
        query_format_accepted = True
    else:
        query_format_accepted = False
    while not query_format_accepted:
        cmddict["query"] = get_argument_list()
        print(f"Query formatting finished:\n{cmdname}['query']=", end="")
        pprint.pprint(cmddict["query"], indent=4)
        query_format_accepted = get_response_yesno(f"Accept format [Y] or re-do[n]?", default='y')
    
    if cmddict["query"] is not None:
        respcount = get_response_posint(f"How many resonses are expected for queries [1]?", min=1, default=1)
        resplist = []
        for idx in range(respcount):
            print(f"Response {idx}/{respcount} type:\n"+SCPI_TYPES_PROMPT)
            resytypeidx = get_response_range("...... Selection:", 1, len(SCPI_TYPES))
            resplist.append(SCPI_TYPES[resytypeidx-1][0])
        cmddict["response"] = resplist
    
    cmddict["help"] = input("Enter command help text/description: s")

    print(f"Command formatting finished:\n{cmdname}=", end="")
    pprint.pprint(cmddict, indent=4)
    do_write = get_response_yesno(f"Accept command and write to file [Y/n]?", default='y')
    if not do_write:
        raise SystemExit("Aborting - nothing written do disk. Do people still say that? Am I old?")
    
    filedata["commands"][cmdname] = cmddict
    update_data_file(filename, filedata)


# file helpers
def get_filename(indent=0):
    """
    Get a SCPI command set filename if none was provided on the command line.
    """
    print("No filename given, please select from the following...")
    scpi_data_files = list_data_files("SCPI_*")
    idx = 0 # so its at this level... we can use it later.
    for idx, filename in enumerate(scpi_data_files):
        print(f"[{idx:2d}] {filename}")
    print(f"[{idx+1:2d}] Abort and Exit")
    fnum = get_response_range(f"Enter File Number: ", 0, idx)

    return scpi_data_files[fnum]

def load_file(filename,indent=0):
    try:
        filedata = load_data_file(filename)
    except FileNotFoundError:
        raise SystemExit(f"Selected file ({filename}) not found.")
    print(f"Loaded {filename}.")
    if "commands" not in filedata:
        raise SystemExit("> No commands dictionary found. Check file format. ")
    return filedata

# command parts helpers
def get_argument_list() -> None | list:   
    argset =  []
    argsetcount = get_response_posint("How many arguments [0]?",0)
    argidx = 0
    for argidx in range(argsetcount):
        print(f"Adding argument {argidx+1}/{argsetcount}:")
        argset.append(dict(
            requried= get_response_yesno("... Required [y/N]?",'n'),
        )) # the rest need more input... cant inline yet...
        print(f"... Argument Type\n"+SCPI_TYPES_PROMPT)
        argtypeidx = get_response_range("...... Selection:", 1, len(SCPI_TYPES))
        argset[argidx]["type"] = SCPI_TYPES[argtypeidx-1][0]
        argdefault = get_response_oftype(f"... Default Value (leave blank for 'No Default'): ",
                                         SCPI_TYPES[argtypeidx-1][0], allowblank=True)
        if argdefault is not None:
            argset[argidx]["default"] = argdefault
        if argset[argidx]["type"] in ('int', 'float') and get_response_yesno(f"... Bound input to specific range? [y/N]",'n'):
            range_min = get_response_float("...... Minimum Bound: ")
            range_min = int(range_min) if argset[-1]["type"] == 'int' else float(range_min)
            range_max = get_response_float("...... Maximum Bound: ", min=range_min)
            range_max = int(range_max) if argset[-1]["type"] == 'int' else float(range_max)
            argset[argidx]["range"] = [range_min, range_max]
        if not argset[argidx].get("range", False) and \
                argset[argidx]["type"] != 'bool' and \
                get_response_yesno(f"... Specify list of valid inputs? [y/N]",'n'):
            resp_raw = input("...... Enter list of values separated by spaces: ")
            argset[argidx]["values"] = resp_raw.split(" ")
        # allow last argument to be variadic...
    if get_response_yesno(f"... Is this (last) argument variadic [y/N]?", default='n'):
        argset[argidx]["varaidic"] = True
    return argset

# responce getter helpers
def get_response_range(prompt: str, min: int, max: int, exit_val: int | None =None) -> int:
    valid_resp = False
    exit_val = max+1 if exit_val is None else exit_val
    this_resp = exit_val
    while not valid_resp:
        resp = input(prompt+" ")
        try: 
            this_resp = int(resp)
        except ValueError as e:
            this_resp = None
        else:
            if this_resp == exit_val:
                pass
            elif (this_resp > max) or (this_resp < min):
                print(f"Invalid Selection: Out of range ({min}-{max}), got {this_resp}")
                this_resp = None
        finally:
            valid_resp = (this_resp is not None)
    if (this_resp == exit_val) or this_resp is None:
        raise SystemExit()
    return this_resp

def get_response_yesno(prompt: str, default: str) -> bool:
    valid_resp = False
    this_resp = default
    while not valid_resp:
        this_resp = input(prompt+" ") or default
        valid_resp =  this_resp.lower() in ('y','n')
        if not valid_resp:
            print(f"Invalid Selection")
    return this_resp.lower() == 'y'

def get_response_posint(prompt: str, default: int, min: int|None=0, max: int|None=None) -> int:
    valid_resp = False
    this_resp = default
    while not valid_resp:
        this_resp = input(prompt+" ") or default
        try:
            this_resp = int(this_resp)
        except ValueError:
            valid_resp = False
            print(f"Invalid Entry: Cannot convert {this_resp} to integer.")
        else:
            loop_max = max if max is not None else this_resp
            loop_min = min if min is not None else this_resp
            if (this_resp > loop_max) or (this_resp < loop_min):
                valid_resp = False
                print(f"Invalid Entry: Input out of range, needs to satisfy " +
                      ("" if min is None else f"min({min}) <") +
                      (f" input({this_resp}) ") +
                      ("" if max is None else f" < max({max})")) 
            else:
                valid_resp = True  
    return this_resp #type: ignore

def get_response_float(prompt: str, min=None, max=None) -> float:
    valid_resp = False
    this_resp = None
    while not valid_resp:
        this_resp = input(prompt+" ")
        try:
            this_resp = float(this_resp)
        except ValueError:
            valid_resp = False
            print(f"Invalid Entry: Cannot convert {this_resp} to numeric.")
        else:
            loop_max = max if max is not None else this_resp
            loop_min = min if min is not None else this_resp
            if (this_resp > loop_max) or (this_resp < loop_min):
                valid_resp = False
                print(f"Invalid Entry: Input out of range, needs to satisfy " +
                      ("" if min is None else f"min({min}) <") +
                      (f" input({this_resp}) ") +
                      ("" if max is None else f" < max({max})")) 
            else:
                valid_resp = True
 
    return this_resp #type: ignore

def get_response_oftype(prompt: str, typev: str, allowblank: bool=True):
    valid_resp = False
    this_resp = None
    func_conv = next((f for n, h, f in SCPI_TYPES if n == typev), None)
    if func_conv is None:
        raise ValueError(f"Undefined SCPI type {typev} - check your code noob")
    
    while not valid_resp:
        this_resp = input(prompt+" ")
        if (this_resp is None) or (allowblank and this_resp==""):
            return None
        try:
            this_resp = func_conv(this_resp)
        except Exception:
            print(f"Input not valid for type {typev}: {this_resp}")
            valid_resp = False
        else:
            valid_resp = True
    return this_resp

# parser build
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

    # ---- add command ----
    add_parser = subparsers.add_parser(
        "add",
        help="Add command.",
    )
    add_parser.add_argument(
        "command_name",
        metavar="name",
        help='Command name to add.',
    )
    add_parser.add_argument(
        "-f", "--scpi_file",
        dest="file",
        metavar="file",
        help='Optional file to add command to.',
        required=False,
        default=None
    )
    add_parser.set_defaults(func=handle_add)

    return parser

def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Dispatch to the handler function for the chosen subcommand
    return args.func(args) or 0
