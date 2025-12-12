HELP_TEXT = """
Simple command line interface for adding scpi commands.

Commands
add COMMAND [FILE]: Add a command. Two arguments, COMMAND and optional FILE to add to.
"""

import argparse
import pprint

from pylab.utilities import list_data_files, load_data_file

GENERIC_ERROR_RETURN = 1

SCPI_TYPES = (("bool", "True/False, 1/0, and ON/OFF."), 
              ("int", "Integer or convertable to integer."),
              ("float", "Floating point numeric."), 
              ("str", "Strings."))

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
    cmddict["set"] = get_set_format()

    pprint.pprint(cmddict)

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
    fnum = get_responce_range(f"Enter File Number: ", 0, idx)

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
def get_set_format() -> None | list:
    hasset = get_responce_yesno("Does this command support sets [Y/n]?",'y')
    if not hasset:
        print("Set format done.")
        return None
    
    argtypechoice_prompt = "\n".join(
        f"...... [{idx+1:2d}] {key} - {val}" for idx, (key,val) in enumerate(SCPI_TYPES)
    ) + f"\n...... [{len(SCPI_TYPES)+1:2d}] Abort and Exit"
    argset =  []
    argsetcount = get_responce_posint("How many set arguments [0]?",0)
    for argidx in range(argsetcount):
        print(f"Adding argument {argidx+1}/{argsetcount}:")
        argset.append(dict(
            requried= get_responce_yesno("... Required [y/N]?",'n'),
        )) # the rest need more input... cant inline yet...
        print(f"... Argument Type\n"+argtypechoice_prompt)
        argtypeidx = get_responce_range("...... Selection:", 1, len(SCPI_TYPES))
        argset[-1]["type"] = SCPI_TYPES[argtypeidx-1][0]
    return argset

# responce getter helpers
def get_responce_range(prompt: str, min: int, max: int, exit_val: int | None =None) -> int:
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

def get_responce_yesno(prompt: str, default: str) -> bool:
    valid_resp = False
    this_resp = default
    while not valid_resp:
        this_resp = input(prompt+" ") or default
        valid_resp =  this_resp.lower() in ('y','n')
        if not valid_resp:
            print(f"Invalid Selection")
    return this_resp == 'y'

def get_responce_posint(prompt: str, default: int, max: int=0) -> int:
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
            if max:
                if this_resp > max:
                    valid_resp = False
                    print(f"Invalid Entry: Input {this_resp} greater than max allowed ({max}).") 
                else:
                    valid_resp = True
            else:
                valid_resp = True      
    return this_resp #type: ignore

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
