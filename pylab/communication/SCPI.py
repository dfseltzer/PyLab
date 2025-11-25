"""
Helpers for parsing and formatting SCPI commands
"""

class CommandValidator(object):
    def __init__(self, command_set) -> None:
        self._command_set = command_set

    def write_string(self, cmd_base, *args):
        # Always use the base command (without '?') for lookup
        base = cmd_base[:-1] if cmd_base.endswith('?') else cmd_base
        if base not in self._command_set:
            raise KeyError(f"Command '{base}' not found in command set.")
        cmd_info = self._command_set[base]
        arg_defs = cmd_info.get('arguments', [])
        # Numeric suffix support
        cmd_str = base
        used_suffix = False
        if cmd_info.get('numeric_suffix'):
            suffix_idx = cmd_info.get('suffix_argument', 0)
            if len(args) > suffix_idx:
                suffix_val = args[suffix_idx]
                cmd_str = f"{base}{suffix_val}"
                args = args[:suffix_idx] + args[suffix_idx+1:]
                used_suffix = True
            else:
                default = arg_defs[suffix_idx].get('default')
                if default is not None:
                    cmd_str = f"{base}{default}"
                    used_suffix = True
                else:
                    raise ValueError(f"Missing required suffix argument for '{base}'.")
        # Argument count/required check
        # If we used a suffix, remove that argument from arg_defs for validation
        if used_suffix:
            arg_defs = arg_defs[:suffix_idx] + arg_defs[suffix_idx+1:]
        required_args = [a for a in arg_defs if a.get('required', False)]
        min_args = len(required_args)
        max_args = len(arg_defs)
        variadic = arg_defs[-1].get('variadic', False) if arg_defs else False
        if not variadic and not (min_args <= len(args) <= max_args):
            raise ValueError(f"Command '{base}' expects between {min_args} and {max_args} arguments, got {len(args)}.")
        if variadic and len(args) < min_args:
            raise ValueError(f"Command '{base}' expects at least {min_args} arguments, got {len(args)}.")
        # Type/values/range validation
        for i, arg_def in enumerate(arg_defs):
            if i >= len(args):
                if arg_def.get('required', False):
                    raise ValueError(f"Missing required argument {i} for '{base}'.")
                continue
            val = args[i]
            typ = arg_def['type']
            if typ == 'bool':
                if not (isinstance(val, (bool, int)) or (isinstance(val, str) and val.upper() in ['ON','OFF','TRUE','FALSE','0','1'])):
                    raise TypeError(f"Argument {i} for '{base}' expects bool, got {val!r}.")
            elif typ == 'int':
                try:
                    ival = int(val)
                except Exception:
                    raise TypeError(f"Argument {i} for '{base}' expects int, got {val!r}.")
                rng = arg_def.get('range')
                if rng and ((rng[0] is not None and ival < rng[0]) or (rng[1] is not None and ival > rng[1])):
                    raise ValueError(f"Argument {i} for '{base}' out of range {rng}: {ival}")
            elif typ == 'float':
                try:
                    fval = float(val)
                except Exception:
                    raise TypeError(f"Argument {i} for '{base}' expects float, got {val!r}.")
                rng = arg_def.get('range')
                if rng and ((rng[0] is not None and fval < rng[0]) or (rng[1] is not None and fval > rng[1])):
                    raise ValueError(f"Argument {i} for '{base}' out of range {rng}: {fval}")
            elif typ == 'str':
                if not isinstance(val, str):
                    raise TypeError(f"Argument {i} for '{base}' expects str, got {val!r}.")
                vals = arg_def.get('values')
                if vals and val not in vals:
                    raise ValueError(f"Argument {i} for '{base}' expects one of {vals}, got {val!r}.")
        # Format command string
        if arg_defs and len(args) > 0:
            if variadic:
                fixed = len(arg_defs) - 1
                fixed_args = args[:fixed]
                variadic_args = args[fixed:]
                all_args = [str(a) for a in fixed_args] + [str(a) for a in variadic_args]
                cmd_str = f"{cmd_str} " + ",".join(all_args)
            else:
                cmd_str = f"{cmd_str} " + ",".join(str(a) for a in args)
        # If original cmd_base had '?', add it back
        if cmd_base.endswith('?') and not cmd_str.endswith('?'):
            cmd_str += '?'
        return cmd_str

    def query_string(self, cmd_base, *args):
        # Always use the base command (without '?') for lookup and formatting
        base = cmd_base[:-1] if cmd_base.endswith('?') else cmd_base
        cmd_str = self.write_string(base, *args)
        if not cmd_str.endswith('?'):
            cmd_str += '?'
        return cmd_str

    def parse_responce(self, cmd_string, resp):
        """
        takes the command as sent to the instrumnet (cmd_string), and the instumment responce.
        Formats the response into pythonic data types and returns them.
        """
        # Find the command base (strip numeric suffixes and arguments)
        base = cmd_string.split()[0]
        import re
        # Remove trailing '?' for lookup
        base = base[:-1] if base.endswith('?') else base
        # Remove numeric suffix if present
        base = re.sub(r'\d+$', '', base)
        if base not in self._command_set:
            raise KeyError(f"Command '{base}' not found in command set.")
        cmd_info = self._command_set[base]
        resp_defs = cmd_info.get('response', [])
        # If no response definition, return raw
        if not resp_defs:
            return resp
        # If only one response, return single value
        if len(resp_defs) == 1:
            typ = resp_defs[0]['type']
            return self._parse_single_response(typ, resp, resp_defs[0])
        # Otherwise, split and parse each
        parts = [p.strip() for p in str(resp).split(',')]
        if len(parts) != len(resp_defs):
            raise ValueError(f"Response length mismatch for '{base}': expected {len(resp_defs)}, got {len(parts)}")
        return [self._parse_single_response(d['type'], v, d) for d, v in zip(resp_defs, parts)]

    def _parse_single_response(self, typ, val, defn):
        if typ == 'bool':
            if isinstance(val, bool):
                return val
            if isinstance(val, int):
                return bool(val)
            if isinstance(val, str):
                if val.upper() in ['ON', 'TRUE', '1']:
                    return True
                if val.upper() in ['OFF', 'FALSE', '0']:
                    return False
            raise ValueError(f"Cannot parse bool from {val!r}")
        elif typ == 'int':
            return int(val)
        elif typ == 'float':
            return float(val)
        elif typ == 'str':
            vals = defn.get('values')
            if vals and val not in vals:
                raise ValueError(f"Response expects one of {vals}, got {val!r}.")
            return val
        else:
            return val
