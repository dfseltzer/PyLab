"""
Abstract base classes for devices.  Should never be instantiated alone.  Use by devices
to ensure a consistent interface.
"""

import logging
from abc import ABC, abstractmethod
from ..communication.connectionHandler import getConnection
from ..communication.SCPI import CommandValidator
from .exceptions import UnknownCommandError

logger = logging.getLogger(__name__)

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
        self._cmd_validator = CommandValidator(command_file)

    @property
    def name(self):
        return self._cnx.name
    
    @property
    def address(self):
        return self._cnx.address

    @property
    def connection_status(self):
        return self._cnx.status

    def get_command_def(self, command):
        """Return the raw command definition from the validator."""
        return self._cmd_validator.get(command)

    def _normalize_set_value(self, command, value):
        """
        Clamp or normalize a set value according to the command's metadata.
        Supports MIN/MAX tokens and numeric range clamping; logs a warning when clamping.
        """
        try:
            cmd_def = self.get_command_def(command)
        except KeyError:
            return value

        arg_defs = cmd_def.get("set") or []
        if not arg_defs:
            return value
        arg_def = arg_defs[0]
        arg_type = arg_def.get("type")
        vals = arg_def.get("values") or []
        rng = arg_def.get("range") or [None, None]

        # Handle token values (MIN/MAX)
        if isinstance(value, str) and value.upper() in {"MIN", "MAX"}:
            if value.upper() == "MIN" and rng[0] is not None:
                return rng[0]
            if value.upper() == "MAX" and rng[1] is not None:
                return rng[1]
            return value

        if arg_type in ("float", "int"):
            try:
                num = float(value) if arg_type == "float" else int(value)
            except Exception:
                return value
            low, high = rng
            clamped = num
            if low is not None and num < low:
                logger.warning(f"Clamping {command} value {num} to min {low}")
                clamped = low
            if high is not None and clamped > high:
                logger.warning(f"Clamping {command} value {clamped} to max {high}")
                clamped = high
            return clamped

        return value

    def write(self, command, *args):
        """
        Write a command to the device after validating against the command set.
        Args:
            command (str): The command key to send (must be in command_set)
            *args: Arguments to fill in for the command parameters
        Raises:
            UnknownCommandError: If the command is not in the command set
            Exception: If the write operation fails
        Returns:
            bool: True if write succeeded, False otherwise
        """
        try:
            normed = [self._cmd_validator.normalize_value(command, a) for a in args]
            cmd_str = self._cmd_validator.validate_command(command, *normed)
        except KeyError:
            raise UnknownCommandError(command, known_commands=self._cmd_validator.commands.keys())

        self._cnx.write(cmd_str)
        return True
        
    def read(self):
        """
        Read a response from the device.
        Raises:
            Exception: If the read operation fails
        """
        return self._cnx.read()
        
    def query(self, command, *args):
        """
        Write a command to the device and read the response.
        Args:
            command (str): The command key to send (must be in command_set)
            *args: Arguments to fill in for the command parameters
        """
        self.write(command, *args)
        return self.read()

    def open(self):
        """Open the underlying connection."""
        return self._cnx.open()

    def close(self):
        """Close the underlying connection."""
        return self._cnx.close()

    def reset_connection(self):
        """Reset the underlying connection."""
        return self._cnx.reset()

    def __del__(self):
        try:
            self._cnx.close()
        except:
            logger.warning(f"{self.name} failed to close connection in __del__")
