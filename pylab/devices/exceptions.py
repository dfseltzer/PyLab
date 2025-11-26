"""
Custom exceptions for device modules.
"""

class UnknownCommandError(KeyError):
    """
    Raised when a command is not found in the device's supported SCPI set.
    """
    def __init__(self, command: str, known_commands=None):
        self.command = command
        self.known_commands = list(known_commands) if known_commands is not None else []
        super().__init__(self.__str__())

    def __str__(self) -> str:
        if self.known_commands:
            # Only show a small sample to avoid overly long error messages.
            sample = ", ".join(sorted(self.known_commands)[:10])
            return f"Unknown command '{self.command}'. Known commands include: {sample}"
        return f"Unknown command '{self.command}'."
