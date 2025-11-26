"""
DC Load Devices
"""

from abc import ABC, abstractmethod

from .exceptions import UnknownCommandError

class DCLoad(MetaClass=ABC):
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
    def voltage(self) -> float:
        raise UnknownCommandError("VOLTAGE?")
    
    @voltage.setter
    def voltage(self, value: float):
        raise UnknownCommandError(f"VOLTAGE {value}")

    @property
    def current(self) -> float:
        raise UnknownCommandError("CURRENT?")
    
    @current.setter
    def current(self, value: float):
        raise UnknownCommandError(f"CURRENT {value}")
    
    @property
    def power(self) -> float:
        raise UnknownCommandError("POWER?")
    
    @power.setter
    def power(self, value: float):
        raise UnknownCommandError(f"POWER {value}")
    