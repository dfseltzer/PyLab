"""
Keysight Devices
"""
import logging
logger = logging.getLogger(__name__)

from .base import Source

class N5770A(Source):
    command_file = "SCPI_N5770A"
    command_map = {
        "enabled": ("OUTP", "OUTP:STAT?"),
        "voltage": ("SOUR:VOLT:LEV:IMM:AMPL", "MEAS:VOLT?"),
        "current": ("SOUR:CURR:LEV:IMM:AMPL", "MEAS:CURR?"),
        "power": (None, None)  # Power control not implemented in this command file
    }

    def __init__(self, name, address, connection_type="VISA", **connection_args) -> None:
        super().__init__(name, address, connection_type, **connection_args)
