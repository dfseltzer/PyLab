"""
Abstract base classes for devices.  Should never be instantiated alone.  Use by devices
to ensure a consistent interface.
"""

import logging
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from ..communication.connectionHandler import getConnection
from ..utils.commandValidator import CommandValidator

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
        try:
            cmd_str = self._cmd_validator.validate_command(command, *args)
        except KeyError as e:
            logger.error(f"Command '{command}' not found in command set: {e}")
            return False
        try:
            self._cnx.write(cmd_str)
            return True
        except Exception as e:
            logger.error(f"Failed to write command '{cmd_str}': {e}")
            return False
        
    def read(self):
        """
        Read a response from the device.
        Raises:
            Exception: If the read operation fails
        """
        try:
            response = self._cnx.read()
            return response
        except Exception as e:
            logger.error(f"Failed to read from device: {e}")
            return None
        
    def query(self, command, *args):
        """
        Write a command to the device and read the response.
        Args:
            command (str): The command key to send (must be in command_set)
            *args: Arguments to fill in for the command parameters
        """
        if not self.write(command, *args):
            return None
        return self.read()

    def __del__(self):
        try:
            self._cnx.close()
        except:
            logger.warning(f"{self.name} failed to close connection in __del__")
    