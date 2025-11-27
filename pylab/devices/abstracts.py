"""
Abstract base classes for devices.  Should never be instantiated alone.  Use by devices
to ensure a consistent interface.
"""

import logging
from abc import ABC, abstractmethod
from ..communication.connection_handler import getConnection
from ..communication.scpi import CommandValidator

logger = logging.getLogger(__name__)

class SCPIDevice(ABC):
    required_attributes = ["command_file"]

    def __init__(self, name, address, connection_type, **connection_kwargs) -> None:
        super().__init__()
        self._cnx = getConnection(connection_type)(name, address, **connection_kwargs)
        try:
            self._cnx.open()
        except Exception as e:
            logger.error(f"Failed to open connection with {e}")
        if not self._cnx:
            raise RuntimeError(f"Unable to open connection to instrument!")
        self._cmd_validator = CommandValidator(self.command_file)

    def __init_subclass__(cls, **kwargs):
        super.__init_subclass__(**kwargs)

        for attr in cls.required_attributes:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define '{attr}'") 

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
        cmd_str = self._cmd_validator(command, *args)
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

    def open_connection(self):
        """Open the underlying connection."""
        return self._cnx.open()

    def close_connection(self):
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

class SCPILoad(SCPIDevice):
    @property
    @abstractmethod
    def command_file(self) -> str:
        pass

    def __init_subclass__(cls, **kwargs):
        super.__init_subclass__(**kwargs)

    @property
    @abstractmethod
    def enabled(self) -> bool:
        pass

    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool):
        pass

    @property
    @abstractmethod
    def mode(self) -> str:
        pass

    @mode.setter
    @abstractmethod
    def mode(self, value: str):
        pass

    @property
    @abstractmethod
    def voltage(self) -> float:
        pass

    @voltage.setter
    @abstractmethod
    def voltage(self, value: float):
        pass

    @property
    @abstractmethod
    def current(self) -> float:
        pass

    @current.setter
    @abstractmethod
    def current(self, value: float):
        pass

    @property
    @abstractmethod
    def power(self) -> float:
        pass

    @power.setter
    @abstractmethod
    def power(self, value: float):
        pass

class SCPISource(SCPIDevice):
    @property
    @abstractmethod
    def command_file(self) -> str:
        pass

    def __init_subclass__(cls, **kwargs):
        super.__init_subclass__(**kwargs)

    @property
    @abstractmethod
    def enabled(self) -> bool:
        pass

    @enabled.setter
    @abstractmethod
    def enabled(self, value: bool):
        pass

    @property
    @abstractmethod
    def voltage(self) -> float:
        pass

    @voltage.setter
    @abstractmethod
    def voltage(self, value: float):
        pass

    @property
    @abstractmethod
    def current(self) -> float:
        pass

    @current.setter
    @abstractmethod
    def current(self, value: float):
        pass

    @property
    @abstractmethod
    def power(self) -> float:
        pass

    @power.setter
    @abstractmethod
    def power(self, value: float):
        pass
