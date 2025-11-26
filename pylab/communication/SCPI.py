"""
Helpers for parsing and formatting SCPI commands
"""

import json
from pathlib import Path
from ..utilities import load_data_file


class CommandValidator(object):
    def __init__(self, command_set, default_path=None) -> None:
        # Load common command set first, then overlay the provided device-specific commands
        self._command_set = load_data_file("SCPI_Common.json")["commands"]
        self._command_set.update(load_data_file(command_set)["commands"])

    @property
    def commands(self):
        """Return the underlying command definition mapping."""
        return self._command_set

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

    def __call__(self, command, *args):
        """
        Format and validate a SCPI command. The command may end with '?' (query) or not (set).
        Returns the full SCPI string ready to send.
        """
        is_query = command.endswith("?")
        base = command[:-1] if is_query else command

        if base not in self._command_set:
            raise KeyError(f"Command '{base}' not found in command set.")

        cmd_def = self._command_set[base]
        arg_defs = cmd_def.get("query" if is_query else "set")
        if arg_defs is None:
            raise KeyError(f"Command '{base}' does not support {'queries' if is_query else 'setting'}.")
        response_defs = cmd_def.get("response")
        # Validate query availability
        if is_query and response_defs is None:
            raise KeyError(f"Command '{base}' does not define query response - check command definition.")

        remaining_args = list(args)

        # Argument count checks
        required_args = [a for a in arg_defs if a.get("required", False)]
        min_args = len(required_args)
        max_args = len(arg_defs)
        variadic = arg_defs[-1].get("variadic", False) if arg_defs else False
        if not variadic and not (min_args <= len(remaining_args) <= max_args):
            raise ValueError(f"Command '{base}' expects between {min_args} and {max_args} arguments, got {len(remaining_args)}.")
        if variadic and len(remaining_args) < min_args:
            raise ValueError(f"Command '{base}' expects at least {min_args} arguments, got {len(remaining_args)}.")

        # Type and range/value validation
        for idx, arg_def in enumerate(arg_defs):
            if idx >= len(remaining_args):
                if arg_def.get("required", False):
                    raise ValueError(f"Missing required argument {idx} for '{base}'.")
                continue
            val = remaining_args[idx]
            typ = arg_def.get("type", "str")
            if typ == "bool":
                if isinstance(val, (bool, int)):
                    pass
                elif isinstance(val, str) and val.upper() in ["ON", "OFF", "TRUE", "FALSE", "0", "1"]:
                    pass
                else:
                    raise TypeError(f"Argument {idx} for '{base}' expects bool-like value, got {val!r}.")
            elif typ == "int":
                if isinstance(val, str) and val in arg_def.get("values", []):
                    ival = val  # allow token strings
                else:
                    try:
                        ival = int(val)
                    except Exception:
                        raise TypeError(f"Argument {idx} for '{base}' expects int, got {val!r}.")
                rng = arg_def.get("range")
                if rng and all(isinstance(x, (int, float, type(None))) for x in rng):
                    if (rng[0] is not None and ival < rng[0]) or (rng[1] is not None and ival > rng[1]):
                        raise ValueError(f"Argument {idx} for '{base}' out of range {rng}: {ival}")
            elif typ == "float":
                if isinstance(val, str) and val in arg_def.get("values", []):
                    fval = val  # allow token strings like MIN/MAX
                else:
                    try:
                        fval = float(val)
                    except Exception:
                        raise TypeError(f"Argument {idx} for '{base}' expects float, got {val!r}.")
                rng = arg_def.get("range")
                if rng and all(isinstance(x, (int, float, type(None))) for x in rng):
                    if (rng[0] is not None and fval < rng[0]) or (rng[1] is not None and fval > rng[1]):
                        raise ValueError(f"Argument {idx} for '{base}' out of range {rng}: {fval}")
            elif typ == "str":
                if not isinstance(val, str):
                    raise TypeError(f"Argument {idx} for '{base}' expects str, got {val!r}.")
                vals = arg_def.get("values")
                if vals and val not in vals:
                    raise ValueError(f"Argument {idx} for '{base}' expects one of {vals}, got {val!r}.")

        # Build command string
        cmd_str = base
        if remaining_args:
            if variadic:
                fixed = len(arg_defs) - 1
                fixed_args = remaining_args[:fixed]
                variadic_args = remaining_args[fixed:]
                all_args = [str(a) for a in fixed_args] + [str(a) for a in variadic_args]
                cmd_str = f"{cmd_str} " + ",".join(all_args)
            else:
                cmd_str = f"{cmd_str} " + ",".join(str(a) for a in remaining_args)

        if is_query and not cmd_str.endswith("?"):
            cmd_str += "?"
        return cmd_str
