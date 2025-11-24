"""
Abstract base classes for devices.  Should never be instantiated alone.  Use by devices
to ensure a consistent interface.
"""

import logging
logger = logging.getLogger(__name__)

from abc import ABC, abstractmethod
from ..communication.connectionHandler import getConnection
from ..utilities import load_data_file

class Device(ABC):
    def __init__(self, name, address, command_file_path,
                 connection_type="VISA", connection_args=dict()) -> None:
        super().__init__()
        self._cnx = getConnection(connection_type)(name, address, **connection_args)
        self._command_set = None
        self._command_set = load_data_file(command_file_path)

    @property
    def name(self):
        return self._cnx.name
    
    @property
    def address(self):
        return self._cnx.address

    @property
    def connection_status(self):
        return self._cnx.status

    def __del__(self):
        try:
            self._cnx.close()
        except:
            logger.warning(f"{self.name} failed to close connection in __del__")

    @property
    @abstractmethod
    def enabled(self):
        pass

    @enabled.setter
    @abstractmethod
    def enabled(self, val):
        pass
    

class DCLoad(Device):
    pass

class DCSupply(Device):
    pass

class Oscilloscope(Device):
    pass

class Multimeter(Device):
    pass