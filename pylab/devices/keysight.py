"""
Keysight Devices
"""
import logging
logger = logging.getLogger(__name__)

from .abstracts import SCPISource

class N5770A(SCPISource):
    command_file = "SCPI_N5770A"

    def __init__(self, name, address, connection_type="VISA", **connection_args) -> None:
        super().__init__(name, address, connection_type, **connection_args)

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

    @property
    def power(self) -> float:
        raise NotImplementedError("Power query not defined in SCPI_N5770A command file.")

    @power.setter
    def power(self, value: float):
        raise NotImplementedError("Power set not defined in SCPI_N5770A command file.")
