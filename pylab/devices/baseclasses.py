"""
Abstract base classes for devices.  Should never be instantiated alone.  Use by devices
to ensure a consistent interface.
"""

import logging
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from ..communication.connectionHandler import getConnection
from ..utilities import load_data_file

class SCPIDevice(ABC):
    def __init__(self, name, address, command_file,
                 connection_type="VISA", **connection_kwargs) -> None:
        super().__init__()
        self._cnx = getConnection(connection_type)(name, address, **connection_kwargs)
        try:
            self._cnx.open()
        except Exception as e:
            logger.error(f"Failed to open connection with {e}")
        if not self._cnx:
            raise RuntimeError(f"Unable to open connection to instrument!")
        self._command_set = load_data_file(command_file)["commands"]

    @property
    def name(self):
        return self._cnx.name
    
    @property
    def address(self):
        return self._cnx.address

    @property
    def connection_status(self):
        return self._cnx.status

    def write(self, command, *args):
        """
        Write a command to the device after validating against the command set.
        Args:
            command (str): The command key to send (must be in command_set)
            *args: Arguments to fill in for the command parameters
        Raises:
            KeyError: If the command is not in the command set
            Exception: If the write operation fails
        Returns:
            bool: True if write succeeded, False otherwise
        """
        commands = self._command_set
        if command not in commands:
            logger.error(f"Command '{command}' not found in command set for {self.name}.")
            raise KeyError(f"Command '{command}' not found in command set.")
        cmd_entry = commands[command]
        cmd_str = cmd_entry['command']
        params = cmd_entry.get('parameters', {})
        param_names = list(params.keys())

        # Determine required and optional parameters
        required_params = [k for k, v in params.items() if v.get('required', False)]
        optional_params = [k for k, v in params.items() if not v.get('required', False)]
        min_args = len(required_params)
        max_args = len(param_names)
        if not (min_args <= len(args) <= max_args):
            logger.error(f"Command '{command}' expects between {min_args} and {max_args} arguments (required: {required_params}, optional: {optional_params}), got {len(args)}.")
            raise ValueError(f"Command '{command}' expects between {min_args} and {max_args} arguments (required: {required_params}, optional: {optional_params}), got {len(args)}.")
        
        # Parameter type validation
        for i, (arg, pname) in enumerate(zip(args, param_names)):
            expected_type = params[pname].get('type', 'str')
            type_map = {'int': int, 'float': float, 'str': str, 'bool': (bool, int, str)}
            py_type = type_map.get(expected_type, str)
            if expected_type == 'bool':
                if isinstance(arg, (bool, int)):
                    pass
                elif isinstance(arg, str) and arg.upper() in ['ON', 'OFF', 'TRUE', 'FALSE', '0', '1']:
                    pass
                else:
                    logger.error(f"Parameter '{pname}' for command '{command}' expects type 'bool' (0/1/ON/OFF/True/False), got value '{arg}' of type '{type(arg).__name__}'.")
                    raise TypeError(f"Parameter '{pname}' for command '{command}' expects type 'bool' (0/1/ON/OFF/True/False), got value '{arg}' of type '{type(arg).__name__}'.")
            else:
                try:
                    _ = py_type(arg)
                except Exception:
                    logger.error(f"Parameter '{pname}' for command '{command}' expects type '{expected_type}', got value '{arg}' of type '{type(arg).__name__}'.")
                    raise TypeError(f"Parameter '{pname}' for command '{command}' expects type '{expected_type}', got value '{arg}' of type '{type(arg).__name__}'.")
        if param_names and len(args) > 0:
            try:
                cmd_str = f"{cmd_str} " + ",".join(str(arg) for arg in args)
            except Exception as e:
                logger.error(f"Failed to format command '{command}' with args={args}: {e}")
                raise
        try:
            result = self._cnx.write(cmd_str)
            logger.info(f"Sent command to {self.name}: {cmd_str} | params: {dict(zip(param_names, args))}")
            return result
        except Exception as e:
            logger.error(f"Failed to write command '{cmd_str}' to {self.name}: {e} | params: {dict(zip(param_names, args))}")
            return False

    def __del__(self):
        try:
            self._cnx.close()
        except:
            logger.warning(f"{self.name} failed to close connection in __del__")

    pass