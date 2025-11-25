"""
VISA based communication wrapper
"""

import pyvisa
import logging
logger = logging.getLogger(__name__)

from .connection import Connection
from .connection import Status

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
    def __init__(self, name, address, timeout=5) -> None:
        super().__init__(name, address)
        self._timeout = timeout
        self._pyvisa_manager = ResourceManager()
        self._pyvisa_resource = None
    
    def open(self) -> Status:
        logger.info(f"{self}: Opening...")
        self._pyvisa_resource = self._pyvisa_manager.open(self.address)
        self.timeout = self._timeout
        self._status = Status.OPEN
        logger.info(f"{self}: Opened as {self._pyvisa_resource}... testing connection")
        resp = self.query("*IDN?")
        if resp is None:
            self._status = Status.UNKNOWN
            logger.error(f"{self} unable to verify connection... unknown issue...")
        else:
            logger.info(f"{self} *IDN? respnce received: {resp}.  Connection probably OK.")
        return self._status

    def close(self) -> Status:
        if self._pyvisa_resource is not None:
            try:
                self._pyvisa_resource.close()
                self._status = Status.CLOSED
            except Exception as e:
                logger.error(f"Failed to close {self} with exception {e}. Changing status to UNKNOWN.")
                self._status = Status.UNKNOWN
            self._pyvisa_resource = None
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

    def read(self) -> str | None:
        if not self:
            logger.error(f"{self}: Unable to write to connection... status is {self.status}")
            return None
        
        try:
            response = self._pyvisa_resource.read()
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
            self._pyvisa_resource.write(command)
            return True
        except Exception as e:
            self._status = Status.UNKNOWN
            logger.error(f"{self} failed to write command {command} with {e} - setting status to UNKNOWN")
            return False
    
    def query(self, command) -> str | None:
        if self and (self._pyvisa_resource is not None):
            return self._pyvisa_resource.query(command)
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
        if self._pyvisa_resource is not None:
            try:
                self._pyvisa_resource.timeout = self._timeout
            except Exception as e:
                logger.error(f"{self}: Failed to set timout value with {e}")

class VISAConnectionBlank(Connection):
    def __init__(self, name, address, timeout=5) -> None:
        super().__init__(name, address)
        self._timeout = timeout
        self._status = Status.OPEN
        logger.info(f"[BLANK] Created VISAConnectionBlank for {name} at {address}")

    def open(self) -> Status:
        logger.info(f"[BLANK] Open called for {self}")
        self._status = Status.OPEN
        return self._status

    def close(self) -> Status:
        logger.info(f"[BLANK] Close called for {self}")
        self._status = Status.CLOSED
        return self._status

    def reset(self) -> Status:
        logger.info(f"[BLANK] Reset called for {self}")
        self._status = Status.OPEN
        return self._status

    def read(self, value) -> str | None:
        logger.info(f"[BLANK] Read called for {self} with value={value}")
        return value

    def write(self, command) -> bool:
        logger.info(f"[BLANK] Write called for {self} with command={command}")
        return True

    def query(self, *args) -> str | None:
        logger.info(f"[BLANK] Query called for {self} with args={args}")
        return args[1] if len(args) > 1 else None

    @property
    def timeout(self) -> int | float:
        return self._timeout

    @timeout.setter
    def timeout(self, val):
        if val <= 0:
            raise ValueError(f"{self}: Timeout must be > 0")
        self._timeout = val
        logger.info(f"[BLANK] Timeout set to {val} for {self}")
