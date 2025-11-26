"""
Mock connection for offline testing without hardware.
"""
import logging
from collections import deque
from .connection import Connection, Status

logger = logging.getLogger(__name__)


class MockConnection(Connection):
    def __init__(self, name, address=None, scripted_responses=None) -> None:
        super().__init__(name, address or "MOCK")
        self._status = Status.CLOSED
        self._write_log = []
        self._responses = deque(scripted_responses or [])

    def open(self) -> Status:
        self._status = Status.OPEN
        return self._status
    
    def close(self) -> Status:
        self._status = Status.CLOSED
        return self._status

    def reset(self) -> Status:
        self._write_log.clear()
        self._responses.clear()
        self._status = Status.OPEN
        return self._status

    def read(self, *args, **kwargs) -> str | None:
        if not self:
            logger.error(f"{self}: Unable to read; status is {self.status}")
            return None
        if self._responses:
            return str(self._responses.popleft())
        return ""

    def write(self, command, *args, **kwargs) -> bool:
        if not self:
            logger.error(f"{self}: Unable to write; status is {self.status}")
            return False
        self._write_log.append(str(command))
        return True

    def query(self, command) -> str | None:
        if self.write(command):
            return self.read()
        return None

    @property
    def writes(self):
        """Return list of commands written so far."""
        return list(self._write_log)

    def preload_responses(self, responses):
        """Preload responses to return on subsequent reads/queries."""
        self._responses.extend(responses)
