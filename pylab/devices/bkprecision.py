"""
BK Precision Devices
"""
import logging
logger = logging.getLogger(__name__)

from .base import Load, Source

class BK8616(Load):
    command_file = "SCPI_BK8616" # type: ignore

    command_map = {  # type: ignore
        "enabled": ("INP", "INP?"),
        "mode": ("FUNC", "FUNC?"),
        "voltage": ("VOLT:ON", "MEAS:VOLT"),
        "current": ("CURR:ON", "MEAS:CURR"),
        "power": ("POW", "MEAS:POW")
    } 

    def __init__(self, name, address, cnx_type="VISA", cmd_type="SCPI", **cnx_args) -> None:
        super().__init__(name, cnx_type, address, cmd_type, self.command_file, **cnx_args)
        
    
class BK9129B(Source):
    command_file = "SCPI_BK9129B"  # type: ignore

    command_map = {  # type: ignore
        "enabled": ("OUTP", "OUTP:STAT?"),
        "voltage": ("VOLT:ON", "MEAS:VOLT"),
        "current": ("CURR", "MEAS:CURR"),
        "power": ("POW", "MEAS:POW")
    }
        
    def __init__(self, name, address, connection_type="VISA", **connection_args) -> None:
        super().__init__(name, address, connection_type, **connection_args)
    
