# connection class outlines

from abc import abstractmethod
from enum import Enum

class Status(Enum):
    """Connection status"""
    UNKNOWN = 0
    OPEN = 1
    CLOSED = 2

    def __bool__(self):
        return self == Status.OPEN

class Connection(object):
    def __init__(self, name, address) -> None:
        self._status = Status.UNKNOWN
        self.name = name
        self.address = address

    @abstractmethod
    def open(self) -> Status:
        pass
    
    @abstractmethod
    def close(self) -> Status:
        pass

    @abstractmethod
    def reset(self) -> Status:
        pass

    @abstractmethod
    def read(self, *args, **kwargs) -> str | None:
        pass

    @abstractmethod
    def write(self, command, *args, **kwargs) -> bool:
        """
        Returns True on success, and False on failure
        """
        pass
    
    @property
    def status(self) -> Status:
        return self._status
    
    def __bool__(self) -> bool:
        return bool(self._status)
     
    def __str__(self) -> str:
        return f"[CNX]({self.status}){self.name}"

    def __repr__(self) -> str:
        return f"[{type(self)}]({self.status}){self.name}:{self.address}"
