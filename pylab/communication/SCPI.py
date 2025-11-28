"""
Helpers for parsing and formatting SCPI commands
"""

import logging
logger = logging.getLogger(__name__)
from ..utilities import load_data_file


class UnknownCommandError(KeyError):
    """
    Raised when a command is not found in the supported SCPI set.
    """
    def __init__(self, command: str, command_set_name=None, info=None):
        self.command = command
        self.command_set_name = command_set_name if command_set_name is not None else "Unknown Command Set"
        self.info = info
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"({self.command_set_name}) Unknown command: '{self.command}'." & (f" Additional info: {self.info}" if self.info else "")


class CommandValidator(object):
    def __init__(self, command_set) -> None:
        # Load common command set first, then overlay the provided device-specific commands
        self._command_set_name = command_set

        self._command_set = load_data_file("SCPI_Common")["commands"]
        self._command_set.update(load_data_file(command_set)["commands"])

    def __contains__(self, command):
        return command in self._command_set

    def __call__(self, command, *args):
        """
        Format and validate a SCPI command. The command may end with '?' (query) or not (set).
        Returns the full SCPI string ready to send.

        NOTE: In definition of commands, an empty list means the format is supported, but that
        there are no arguments for that format.  COnversly, a value of None (null) means that 
        the given format is not supported.
        """
        is_query = command.endswith("?")
        base = command[:-1] if is_query else command

        try:
            cmd_def = self._command_set[base]
        except KeyError:
            raise UnknownCommandError(command, command_set_name=self._command_set_name, info="Base command not found.")
        arg_defs = cmd_def.get("query" if is_query else "set")

        if arg_defs is None:
            # None means not supported.  An empty list means supported but with no arguments.
            raise UnknownCommandError(command, command_set_name=self._command_set_name, 
                                      info="Query format not supported." if is_query else "Set format not supported.")

        response_defs = cmd_def.get("response")
        if is_query and response_defs is None:
            raise UnknownCommandError(command, command_set_name=self._command_set_name, 
                                      info="Command definition error: Query supported but no responce format set.")

        # check edge case where no args age given, and first arg is requied
        # The first agument will never be optional if future arguments are required.
        if not len(args) and len(arg_defs):
            if arg_defs[0].get("required", True):
                raise ValueError(f"{self._command_set_name}:{command}: No arguments, but arguments requried! {arg_defs}")

        # Validate arguments against definitions...
        this_arg_def = 0
        cleaned_args = list()
        for this_arg_val in range(len(args)):
            if this_arg_def >= len(arg_defs): # we ran out of definitions before we ran out of arguments... oops...
                raise ValueError(f"{self._command_set_name}:{command}: Too many arguments supplied? {args} for {arg_defs}")
            # check arg against matched definition
            for this_arg_def in range(this_arg_def, len(arg_defs)):
                is_ok = self.validate_argument(args[this_arg_val], arg_defs[this_arg_def])
                if is_ok: # argument was OK - normalize, then exit inner loop. move onto next one.
                    cleaned_args.append(args[this_arg_val])
                    break
                elif arg_defs[this_arg_def].get("required", True): # not OK, and not optional - ERROR
                    raise ValueError(f"{self._command_set_name}:{command}: Unable to validate {args[this_arg_val]} against definition {arg_defs[this_arg_def]}")  
                else: # not ok, but was not required. try to validate against next argument definition.
                    pass
            if arg_defs[this_arg_def].get("variadic", False): # accepts more than one - dont increment definition yet.
                # these are always the last argument.
                # because of this, edge case were there are arguments after this do not matter.
                pass
            else: # only accepts one of this definition, so increment to next def for next loop.
                this_arg_def = this_arg_def+1
            # on to the next loop... 

        # Build command string
        args_string = ",".join(str(a) for a in cleaned_args)
        cmd_string =  f"{command} " + args_string
        return cmd_string.strip()

    def get(self, command):
        """
        Return the command definition for a base command (no '?' suffix).
        Raises KeyError if not present.
        """
        is_query = command.endswith("?")
        base = command[:-1] if is_query else command
        if base not in self._command_set:
            raise KeyError(f"Command '{base}' not found in command set.")
        return self._command_set[base]

    def validate_argument(self, argument, argument_definition):
        """
        Validates a single argument against the given argument definition.  Returns True if the argument is OK,
        and False if not.
        """
        expected_type = argument_definition.get("type")
        if expected_type is None:
            raise TypeError("Argument definition missing type")

        if argument is None:
            return False

        # Basic type validation
        if expected_type == "bool":
            if isinstance(argument, bool):
                pass
            elif isinstance(argument, (int, float)) and not isinstance(argument, bool):
                if argument not in (0, 1):
                    raise TypeError(f"Expected boolean-like numeric value, got {argument!r}")
            elif isinstance(argument, str):
                if argument.strip().upper() not in {"ON", "OFF", "0", "1", "TRUE", "FALSE"}:
                    raise TypeError(f"Expected boolean-like string value, got {argument!r}")
            else:
                raise TypeError(f"Expected boolean-like value, got {type(argument).__name__}")
        elif expected_type == "int":
            if isinstance(argument, bool) or not isinstance(argument, int):
                raise TypeError(f"Expected int, got {type(argument).__name__}")
        elif expected_type == "float":
            if isinstance(argument, bool) or not isinstance(argument, (int, float)):
                raise TypeError(f"Expected float, got {type(argument).__name__}")
        elif expected_type == "str":
            if not isinstance(argument, str):
                raise TypeError(f"Expected str, got {type(argument).__name__}")
        else:
            raise TypeError(f"Unknown argument type '{expected_type}'")

        # Enumerated allowed values
        if "values" in argument_definition and argument_definition["values"] is not None:
            allowed = argument_definition["values"]
            if isinstance(argument, str):
                if not any((isinstance(v, str) and v.upper() == argument.upper()) or v == argument for v in allowed):
                    return False
            else:
                if argument not in allowed:
                    return False

        # Numeric range validation
        if "range" in argument_definition and argument_definition["range"] is not None:
            try:
                low, high = argument_definition["range"]
            except Exception:
                low = high = None
            if isinstance(argument, (int, float)) and not isinstance(argument, bool):
                if low is not None and isinstance(low, (int, float)) and argument < low:
                    return False
                if high is not None and isinstance(high, (int, float)) and argument > high:
                    return False

        return True
        
