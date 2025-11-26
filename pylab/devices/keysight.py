"""
Keysight Devices
"""
import logging
from .scpidevice import SCPIDevice
from .dcsource import DCSource

logger = logging.getLogger(__name__)


class N5770A(SCPIDevice, DCSource):
    command_file = "SCPI_N5770A"

    def __init__(self, name, address, **connection_args) -> None:
        super().__init__(name, address, self.command_file, connection_type="VISA", **connection_args)

    @property
    def enabled(self) -> bool:
        response = self.query("OUTP:STAT?")
        if response is None:
            return False
        return response.strip() in {"1", "ON", "True", "TRUE"}

    @enabled.setter
    def enabled(self, value: bool):
        self.write("OUTP:STAT", value)

    @property
    def voltage(self) -> float:
        response = self.query("MEAS:VOLT?")
        if response is None:
            return 0.0
        try:
            return float(response.strip())
        except ValueError:
            logger.error(f"Unexpected voltage response: {response!r}")
            return 0.0

    @voltage.setter
    def voltage(self, value: float):
        self.write("SOUR:VOLT:LEV:IMM:AMPL", value)

    @property
    def current(self) -> float:
        response = self.query("MEAS:CURR?")
        if response is None:
            return 0.0
        try:
            return float(response.strip())
        except ValueError:
            logger.error(f"Unexpected current response: {response!r}")
            return 0.0

    @current.setter
    def current(self, value: float):
        self.write("SOUR:CURR:LEV:IMM:AMPL", value)
