"""
DC Source Devices
"""

from abc import ABC, abstractmethod
from .exceptions import UnknownCommandError

class DCSource(ABC):
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
    def power(self) -> float:
        raise UnknownCommandError("POW?")
    
    @power.setter
    def power(self, value: float):
        raise UnknownCommandError(f"POW {value}")