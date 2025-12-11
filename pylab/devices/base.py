"""
Abstract base classes for devices.  Should never be instantiated alone.  Use by devices
to ensure a consistent interface.
"""

import logging
from abc import ABC, abstractmethod
from ..communication import getConnection
from ..communication import getCommandSet

logger = logging.getLogger(__name__)

class Device(ABC):
    """
    Abstract base class for all devices.
    Ensures consistent interface for device communication and command validation.

    Concrete device classes must define the following class attributes:
        - command_file: str - The command set file name for the device.
        - command_map: dict - A mapping of device common commands to their 
            device specific definitions.

    Keys in the command map are treated as properties of each instance. Accessing these
    as a get will issue a query to the device, while setting them will issue a write.

    Command map entries are tuples of (write_command_key, query_command_key).

    """

    required_attributes = ["command_file", "command_map"]

    def __init__(self, name, cnx_type, cnx_address, cmd_type, cmd_file, **cnx_args) -> None:
        super().__init__()

        self._cnx = getConnection(cnx_type)(name, cnx_address, **cnx_args)
        try:
            self._cnx.open()
        except Exception as e:
            logger.error(f"Failed to open connection with {e}")
        if not self._cnx:
            raise RuntimeError(f"Unable to open connection to instrument!")
        self._cmd = getCommandSet(cmd_type)(cmd_file)

    def __init_subclass__(cls, **kwargs):
        super.__init_subclass__(**kwargs)

        for attr in cls.required_attributes:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define '{attr}'") 

    def __setattr__(self, name, value):
        if name in ("command_map", "__dict__", "__class__"): # these items should NOT get intercepted...
            object.__setattr__(self, name, value)
            return

        cmd_map = object.__getattribute__(self, "command_map") # since we are intercepting here...
        if name in cmd_map:
            write_key, _ = cmd_map[name]
            if write_key is None:
                raise AttributeError(f"{self.name}: Command '{name}' is read-only or not implemented.")
            self.write(write_key, value)
        else: # not in map... just try normal set
            object.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if name in ("command_map", "write", "query", "__dict__", "__class__",
            "__setattr__", "__getattribute__", ): # these items should NOT get intercepted...
            return object.__getattribute__(self, name)

        cmd_map = object.__getattribute__(self, "command_map") # since we are intercepting here...
        if name in cmd_map:
            _, query_key = cmd_map[name]
            if query_key is None:
                raise AttributeError(f"{self.name}: Command '{name}' is write-only or not implemented.")
            query = object.__getattribute__(self, "query") # again skip normals since we intercept...
            return query(query_key)
        else: # not in map... just do normal stuff...
            return object.__getattribute__(self, name)

    @property
    def name(self):
        return self._cnx.name
    
    @property
    def address(self):
        return self._cnx.address

    @property
    def connection_status(self):
        return self._cnx.status

    def command_info(self, command):
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

class Load(Device):
    @property
    @abstractmethod
    def command_file(self) -> str:
        pass

    @property
    @abstractmethod
    def command_map(self) -> dict:
        pass

class Source(Device):
    @property
    @abstractmethod
    def command_file(self) -> str:
        pass

    @property
    @abstractmethod
    def command_map(self) -> dict:
        pass

