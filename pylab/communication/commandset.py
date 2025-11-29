
from abc import ABC, abstractmethod
from ..utilities import load_data_file
from enum import Enum

class CommandSetTypes(Enum):
    SCPI = 0

    @staticmethod
    def is_known(val):
        if isinstance(val, CommandSet):
            return True
        if isinstance(val, str):
            return val in CommandSetTypes.__members__
        return False

class CommandSet(ABC):
    required_attributes = ["command_file_common"]

    def __init__(self, _command_set_name) -> None:
        # Load common command set first, then overlay the provided device-specific commands
        self._command_set_name = _command_set_name
        self._command_set = load_data_file(self.command_file_common)["commands"]
        
        device_command_set = load_data_file(self._command_set_name)

        self._command_set.update(device_command_set["commands"])

    def __init_subclass__(cls, **kwargs):
        super.__init_subclass__(**kwargs)

        for attr in cls.required_attributes:
            if not hasattr(cls, attr):
                raise TypeError(f"{cls.__name__} must define '{attr}'") 

    
    def __contains__(self, command):
        return command in self._command_set
    
    def get(self, command, default=None):
        """Return the raw command definition from the command set."""
        return self._command_set.get(command, default)
    
    @abstractmethod
    def validate_command(self, command, *args) -> str:
        """
        Validate a command and its arguments against the command set.
        Raises UnknownCommandError or InvalidCommandArgumentsError on failure.
        Returns the formatted command string on success.
        """
        pass

    @abstractmethod
    def validate_argument(self, argument, argument_definition) -> tuple[bool, str | None]:
        """
        Validates a single argument against the given argument definition.  Returns tuple (is_ok, error_kind)
        where error_kind is "value" when the value is outside accepted ranges/sets, "type" for other validation
        failures, and None when valid.
        """
        pass