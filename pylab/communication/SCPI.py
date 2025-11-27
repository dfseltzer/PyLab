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
    def __init__(self, command: str, known_commands=None):
        self.command = command
        self.known_commands = list(known_commands) if known_commands is not None else []
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.known_commands:
            sample = ", ".join(sorted(self.known_commands)[:10])
            return f"Unknown command '{self.command}'. Known commands include: {sample}"
        return f"Unknown command '{self.command}'."


class CommandValidator(object):
    def __init__(self, command_set, default_path=None) -> None:
        # Load common command set first, then overlay the provided device-specific commands
        self._command_set = load_data_file("SCPI_Common")["commands"]
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
            raise UnknownCommandError(base, known_commands=self._command_set.keys())

        cmd_def = self._command_set[base]
        arg_defs = cmd_def.get("query" if is_query else "set")
        if arg_defs is None:
            raise UnknownCommandError(f"{base}{'?' if is_query else ''}", known_commands=self._command_set.keys())
        response_defs = cmd_def.get("response")
        # Validate query availability
        if is_query and response_defs is None:
            raise UnknownCommandError(f"{base}?", known_commands=self._command_set.keys())

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
        normalized_args = []
        for idx, arg_def in enumerate(arg_defs):
            if idx >= len(remaining_args):
                if arg_def.get("required", False):
                    raise ValueError(f"Missing required argument {idx} for '{base}'.")
                continue
            raw_val = remaining_args[idx]
            val = self.normalize_value(base, raw_val)
            typ = arg_def.get("type", "str")
            if typ == "bool":
                if isinstance(val, (bool, int)):
                    pass
                elif isinstance(val, str) and val.upper() in ["ON", "OFF", "TRUE", "FALSE", "0", "1"]:
                    pass
                else:
                    raise TypeError(f"Argument {idx} for '{base}' expects bool-like value, got {val!r}.")
                normalized_args.append(val)
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
                normalized_args.append(ival)
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
                normalized_args.append(fval)
            elif typ == "str":
                if not isinstance(val, str):
                    raise TypeError(f"Argument {idx} for '{base}' expects str, got {val!r}.")
                vals = arg_def.get("values")
                if vals and val not in vals:
                    raise ValueError(f"Argument {idx} for '{base}' expects one of {vals}, got {val!r}.")
                normalized_args.append(val)

        # Build command string
        cmd_str = base
        args_to_use = normalized_args if normalized_args else remaining_args
        if args_to_use:
            if variadic:
                fixed = len(arg_defs) - 1
                fixed_args = args_to_use[:fixed]
                variadic_args = args_to_use[fixed:]
                all_args = [str(a) for a in fixed_args] + [str(a) for a in variadic_args]
                cmd_str = f"{cmd_str} " + ",".join(all_args)
            else:
                cmd_str = f"{cmd_str} " + ",".join(str(a) for a in args_to_use)

        if is_query and not cmd_str.endswith("?"):
            cmd_str += "?"
        return cmd_str

    def normalize_value(self, command, value):
        """
        Clamp or normalize a value based on command metadata (supports MIN/MAX tokens).
        Returns the possibly modified value.
        """
        is_query = command.endswith("?")
        base = command[:-1] if is_query else command
        if base not in self._command_set:
            return value
        arg_defs = self._command_set[base].get("set") or []
        if not arg_defs:
            return value
        def normalize_single(arg_def, val):
            arg_type = arg_def.get("type")
            rng = arg_def.get("range") or [None, None]
            # token handling
            if isinstance(val, str) and val.upper() == "MIN" and rng[0] is not None:
                logger.warning(f"Normalizing {command} value MIN to {rng[0]}")
                return rng[0]
            if isinstance(val, str) and val.upper() == "MAX" and rng[1] is not None:
                logger.warning(f"Normalizing {command} value MAX to {rng[1]}")
                return rng[1]
            # numeric clamping
            if arg_type in ("float", "int"):
                try:
                    num = float(val) if arg_type == "float" else int(val)
                except Exception:
                    return val
                low, high = rng
                clamped = num
                if low is not None and num < low:
                    logger.warning(f"Clamping {command} value {num} to min {low}")
                    clamped = low
                if high is not None and clamped > high:
                    logger.warning(f"Clamping {command} value {clamped} to max {high}")
                    clamped = high
                # preserve expected type
                return float(clamped) if arg_type == "float" else int(clamped)
            return val

        # normalize across all provided args
        normalized_args = []
        variadic = arg_defs[-1].get("variadic", False)
        for idx, val in enumerate(value if isinstance(value, (list, tuple)) else [value]):
            if idx < len(arg_defs):
                normalized_args.append(normalize_single(arg_defs[idx], val))
            elif variadic:
                normalized_args.append(normalize_single(arg_defs[-1], val))
            else:
                normalized_args.append(val)
        if isinstance(value, (list, tuple)):
            return type(value)(normalized_args)
        return normalized_args[0] if normalized_args else value
