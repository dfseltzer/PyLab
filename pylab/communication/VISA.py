"""
VISA based communication wrapper
"""

import pyvisa
import logging
logger = logging.getLogger(__name__)

from .Connection import Connection
from .Connection import Status

# Update this to change the default resource manager
RESOURCEMANAGER = '@py'

class ResourceManager(object):
    """VISA resource manager singleton.  Should really never be instantiated by users"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, '_initialized'):
            return
        # only do onece, so set flag.
        self._initialized = True
        self.manager = pyvisa.ResourceManager(RESOURCEMANAGER)
        self.intruments = dict() # resource name to object map
        
    def reset(self, really_do_this=False):
        if not really_do_this:
            raise RuntimeError(f"This would close all connections!  Do you really want to do this? If so, pass really_do_this=True.")
        else:
            logger.warning(f"We are really doing this! Closing all instruments...")

        for resource in self.manager.list_opened_resources():
            if resource.resource_name not in self.intruments.keys():
                logger.warning(f"Resource not in open list, but manager sees as open.  Trying to close: {resource.resource_name}")
                try:
                    resource.close()
                except Exception as e:
                    logger.warning(f"Exception when trying to close {resource.resource_name}: {e}")
            else:
                self.intruments[resource.resource_name].close()
        for name, cnx in self.intruments.items():
            if cnx:
                logger.warning(f"Connection thinks its open, but manager does now know it. Trying to close: {name}")
            try:
                cnx.close()
            except Exception as e:
                logger.warning(f"Exception when trying to close {cnx.name}: {e}")
        # get a new one just in case...
        self.manager = pyvisa.ResourceManager(RESOURCEMANAGER)

    def open(self, address):
        resource = self.manager.open_resource(address)
        if resource is None:
            raise RuntimeError(f"Unable to open resource by address: {address}")
        return resource

class VISAConnection(Connection):
    def __init__(self, name, address, timeout=5, *args, **kwargs) -> None:
        super().__init__(name, address, *args, **kwargs)
        
        self._timeout = 5
        
        self.rm = ResourceManager()
        self.resource = None

    def open(self) -> Status:
        logger.info(f"{self}: Opening...")
        self.resource = self.rm.open(self.address)
        self.timeout = self._timeout
        self._status = Status.OPEN
        logger.info(f"{self}: Opened as {self.resource}... testing connection")
        resp = self.query("*IDN?")
        if resp is None:
            self._status = Status.UNKNOWN
            logger.error(f"{self} unable to verify connection... unknown issue...")
        else:
            logger.info(f"{self} *IDN? respnce received: {resp}.  Connection probably OK.")
        return self._status

    def close(self) -> Status:
        if self.resource is not None:
            try:
                self.resource.close()
                self._status = Status.CLOSED
            except Exception as e:
                logger.error(f"Failed to close {self} with exception {e}. Changing status to UNKNOWN.")
                self._status = Status.UNKNOWN
            self.resource = None
            return self._status
        else:
            logger.warning(f"Tried to close connection that does not exist: {self}")
            self._status = Status.CLOSED
            return self._status
    
    def reset(self) -> Status:
        self.close()
        if self.status != Status.CLOSED:
            logger.error(f"Trying to reset connection {self}, but could not close.  Trying to open anyway... ")
        self.open()
        return self.status

    def read(self, *args, **kwargs) -> str | None:
        if not self:
            logger.error(f"{self}: Unable to write to connection... status is {self.status}")
            return None
        
        try:
            response = self.resource.read()
            return response.strip()
        except Exception as e:
            self._status = Status.UNKNOWN
            logger.error(f"{self} failed to read command with {e} - setting status to UNKNOWN")
            return None
    
    def write(self, command) -> bool:
        if not self:
            logger.error(f"{self}: Unable to write to connection... status is {self.status}")
            return False
        
        try:
            self.resource.write(command)
            return True
        except Exception as e:
            self._status = Status.UNKNOWN
            logger.error(f"{self} failed to write command {command} with {e} - setting status to UNKNOWN")
            return False
    
    def query(self, command) -> str | None:
        if self and (self.resource is not None):
            return self.resource.query(command)
        else:
            logger.error(f"{self}: Status is not open - unable to query.")
            return None

    @property
    def timeout(self) -> int | float:
        return self._timeout
    
    @timeout.setter
    def timeout(self, val):
        if val <= 0:
            raise ValueError(f"{self}: Timeout must be > 0")
        self._timeout = val
        if self.resource is not None:
            try:
                self.resource.timeout = self._timeout
            except Exception as e:
                logger.error(f"{self}: Failed to set timout value with {e}")