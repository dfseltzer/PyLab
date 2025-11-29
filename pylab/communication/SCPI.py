"""
SCPI (Standard Commands for Programmable Instruments) command validation and formatting.

SCPI defines command formatting only.

Primarily provides the SCPIValidator class to validate and format SCPI commands
according to a loaded command set definition. Also includes custom exceptions for
various SCPI-related errors.
"""

import logging
logger = logging.getLogger(__name__)
from ..utilities import load_data_file

from .commandset import CommandSet

class SCPIError(Exception):
    """Base class for SCPI-related errors."""
    pass

class SCPIUnknownCommandError(SCPIError):
    """
    Raised when a command is not found in the supported SCPI set. 
    Inputs:
    - command: The unknown command string
    - command_set_name: Name of the command set being used
    - info: Optional additional information about the error
    """
    def __init__(self, command: str, command_set_name=None, info=None):
        self.command = command
        self.command_set_name = command_set_name if command_set_name is not None else "Unknown Command Set"
        self.info = info
        super().__init__(self.__str__())

    def __str__(self) -> str:
        return f"({self.command_set_name}) Unknown command: '{self.command}'." + (f" Additional info: {self.info}" if self.info else "")

class SCPIArgumentError(SCPIError):
    """
    Raised when SCPI command arguments are invalid.
    Inputs:
    - command: The command string
    - argument: The invalid argument value
    - command_definition: The command definition being used to validate
    - info: Optional additional information about the error
    """
    def __init__(self, command: str, argument, command_definition=None, info=None):
        self.command = command
        self.argument = argument
        self.command_definition = command_definition
        self.info = info
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"Invalid argument '{self.argument}' for command '{self.command}'."
        if self.command_definition:
            base += f" Command definition: {self.command_definition}."
        if self.info:
            base += f" Additional info: {self.info}"
        return base

class SCPIArgumentValueError(SCPIError):
    """
    Raised when SCPI command argument values are out of range or invalid.
    Inputs:
    - command: The command string
    - argument: The invalid argument value
    - command_definition: The command definition being used to validate
    - info: Optional additional information about the error
    """
    def __init__(self, command: str, argument, command_definition=None, info=None):
        self.command = command
        self.argument = argument
        self.command_definition = command_definition
        self.info = info
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"Invalid argument value '{self.argument}' for command '{self.command}'."
        if self.command_definition:
            base += f" Command definition: {self.command_definition}."
        if self.info:
            base += f" Additional info: {self.info}"
        return base

class SCPICommandSet(CommandSet):
    command_file_common = "SCPI_Common"

    def __init__(self, command_set) -> None:
        super().__init__(command_set)
  
    def get(self, command):
        """
        Return the command definition for a base command (no '?' suffix).
        Raises KeyError if not present.
        """
        if command.endswith("?"):
            base = command[:-1]
            logger.warning(f"SCPICommandSet.get called with query command {command}; using base command {base} instead.")
        return super().get(base)

    def validate_argument(self, argument, argument_definition):
        """
        Validates a single argument against the given argument definition.  Returns tuple (is_ok, error_kind)
        where error_kind is "value" when the value is outside accepted ranges/sets, "type" for other validation
        failures, and None when valid.
        """
        expected_type = argument_definition.get("type")
        if expected_type is None:
            raise SCPIArgumentError("Definition", argument_definition, info="Argument definition missing type")

        if argument is None:
            return False, "type"

        # Basic type validation
        if expected_type == "bool":
            if isinstance(argument, bool):
                pass
            elif isinstance(argument, (int, float)) and not isinstance(argument, bool):
                if argument not in (0, 1):
                    return False, "type"
            elif isinstance(argument, str):
                if argument.strip().upper() not in {"ON", "OFF", "0", "1", "TRUE", "FALSE"}:
                    return False, "type"
            else:
                return False, "type"
        elif expected_type == "int":
            if isinstance(argument, bool) or not isinstance(argument, int):
                return False, "type"
        elif expected_type == "float":
            if isinstance(argument, bool) or not isinstance(argument, (int, float)):
                return False, "type"
        elif expected_type == "str":
            if not isinstance(argument, str):
                return False, "type"
        else:
            raise SCPIArgumentError("Definition", argument_definition, info=f"Unknown argument type '{expected_type}'")

        # Enumerated allowed values
        if "values" in argument_definition and argument_definition["values"] is not None:
            allowed = argument_definition["values"]
            if isinstance(argument, str):
                if not any((isinstance(v, str) and v.upper() == argument.upper()) or v == argument for v in allowed):
                    return False, "value"
            else:
                if argument not in allowed:
                    return False, "value"

        # Numeric range validation
        if "range" in argument_definition and argument_definition["range"] is not None:
            try:
                low, high = argument_definition["range"]
            except Exception:
                low = high = None
            if isinstance(argument, (int, float)) and not isinstance(argument, bool):
                if low is not None and isinstance(low, (int, float)) and argument < low:
                    return False, "value"
                if high is not None and isinstance(high, (int, float)) and argument > high:
                    return False, "value"

        return True, None

    def validate_command(self, command, *args):
        """
        Format and validate a SCPI command. The command may end with '?' (query) or not (set).
        Returns the full SCPI string ready to send.

        NOTE: In definition of commands, an empty list means the format is supported, but that
        there are no arguments for that format.  COnversly, a value of None (null) means that 
        the given format is not supported.
        """
        is_query = command.endswith("?")
        base = command[:-1] if is_query else command
        logger.debug("Validating SCPI command '%s' (query=%s) args=%s", command, is_query, args)

        try:
            cmd_def = self._command_set[base]
        except KeyError:
            logger.error("SCPI command '%s' not found in command set '%s'", base, self._command_set_name)
            raise SCPIUnknownCommandError(command, command_set_name=self._command_set_name, info="Base command not found.")
        arg_defs = cmd_def.get("query" if is_query else "set")

        if arg_defs is None:
            # None means not supported.  An empty list means supported but with no arguments.
            logger.error("SCPI command '%s' unsupported format (%s)", command, "query" if is_query else "set")
            raise SCPIUnknownCommandError(command, command_set_name=self._command_set_name, 
                                      info="Query format not supported." if is_query else "Set format not supported.")

        response_defs = cmd_def.get("response")
        if is_query and response_defs is None:
            logger.error("SCPI command '%s' has query format but missing response definition", command)
            raise SCPIUnknownCommandError(command, command_set_name=self._command_set_name, 
                                      info="Command definition error: Query supported but no responce format set.")

        # check edge case where no args age given, and first arg is requied
        # The first agument will never be optional if future arguments are required.
        if not len(args) and len(arg_defs):
            if arg_defs[0].get("required", True):
                logger.error("SCPI command '%s' missing required arguments. Definitions: %s", command, arg_defs)
                raise SCPIArgumentError(command, args, arg_defs, info=f"{self._command_set_name}: No arguments, but arguments required! {arg_defs}")

        # Validate arguments against definitions...
        this_arg_def = 0
        matched_args = dict()  # def index -> list of provided values (keeps variadic order)
        for this_arg_val, this_arg in enumerate(args):
            if this_arg_def >= len(arg_defs): # we ran out of definitions before we ran out of arguments... oops...
                logger.error("SCPI command '%s' provided too many arguments: %s for definitions %s", command, args, arg_defs)
                raise SCPIArgumentError(command, args, arg_defs, info=f"{self._command_set_name}: Too many arguments supplied? {args} for {arg_defs}")
            matched_def_index = None
            last_error_kind = None
            # check arg against matched definition
            for candidate_def_idx in range(this_arg_def, len(arg_defs)):
                is_ok, error_kind = self.validate_argument(this_arg, arg_defs[candidate_def_idx])
                if is_ok: # argument was OK - normalize, then exit inner loop. move onto next one.
                    matched_def_index = candidate_def_idx
                    matched_args.setdefault(candidate_def_idx, []).append(this_arg)
                    logger.debug("SCPI command '%s': matched argument %s to definition index %d", command, this_arg, candidate_def_idx)
                    break
                else:
                    last_error_kind = error_kind
                    if arg_defs[candidate_def_idx].get("required", True): # not OK, and not optional - ERROR
                        if error_kind == "value":
                            logger.error("SCPI command '%s' argument %s failed value validation against %s", command, this_arg, arg_defs[candidate_def_idx])
                            raise SCPIArgumentValueError(command, this_arg, arg_defs[candidate_def_idx], info=f"{self._command_set_name}: Unable to validate {this_arg} against definition {arg_defs[candidate_def_idx]}")
                        logger.error("SCPI command '%s' argument %s failed validation against %s", command, this_arg, arg_defs[candidate_def_idx])
                        raise SCPIArgumentError(command, this_arg, arg_defs[candidate_def_idx], info=f"{self._command_set_name}: Unable to validate {this_arg} against definition {arg_defs[candidate_def_idx]}")  
            if matched_def_index is None:
                if last_error_kind == "value":
                    logger.error("SCPI command '%s' argument %s failed all remaining value validations", command, this_arg)
                    raise SCPIArgumentValueError(command, this_arg, arg_defs[this_arg_def:], info=f"{self._command_set_name}: Unable to validate {this_arg} against any remaining argument definitions {arg_defs[this_arg_def:]}")
                logger.error("SCPI command '%s' argument %s failed all remaining validations", command, this_arg)
                raise SCPIArgumentError(command, this_arg, arg_defs[this_arg_def:], info=f"{self._command_set_name}: Unable to validate {this_arg} against any remaining argument definitions {arg_defs[this_arg_def:]}")
            if arg_defs[matched_def_index].get("variadic", False): # accepts more than one - dont increment definition yet.
                # these are always the last argument.
                # because of this, edge case were there are arguments after this do not matter.
                this_arg_def = matched_def_index
            else: # only accepts one of this definition, so increment to next def for next loop.
                this_arg_def = matched_def_index + 1
            # on to the next loop...

        # Fill in defaults for optional arguments that were not provided.
        for def_idx, arg_def in enumerate(arg_defs):
            if def_idx in matched_args:
                continue
            default_is_set = "default" in arg_def and arg_def.get("default") is not None
            if (not arg_def.get("required", True)) and default_is_set:
                is_ok, error_kind = self.validate_argument(arg_def["default"], arg_def)
                if not is_ok:
                    if error_kind == "value":
                        logger.error("SCPI command '%s' default value %s failed value validation against %s", command, arg_def["default"], arg_def)
                        raise SCPIArgumentValueError(command, arg_def["default"], arg_def, info=f"{self._command_set_name}: Default value invalid for definition {arg_def}")
                    logger.error("SCPI command '%s' default value %s failed validation against %s", command, arg_def["default"], arg_def)
                    raise SCPIArgumentError(command, arg_def["default"], arg_def, info=f"{self._command_set_name}: Default value invalid for definition {arg_def}")
                matched_args[def_idx] = [arg_def["default"]]
                logger.debug("SCPI command '%s': inserting default for arg index %d -> %s", command, def_idx, arg_def["default"])

        # Build command string
        cleaned_args = list()
        for def_idx, arg_def in enumerate(arg_defs):
            if def_idx not in matched_args:
                continue
            if arg_def.get("variadic", False):
                cleaned_args.extend(matched_args[def_idx])
            else:
                cleaned_args.append(matched_args[def_idx][0])
        args_string = ",".join(str(a) for a in cleaned_args)
        cmd_string =  f"{command} " + args_string
        logger.debug("SCPI command '%s' formatted as: %s", command, cmd_string.strip())
        return cmd_string.strip()
