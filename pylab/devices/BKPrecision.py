"""
BK Precision Devices
"""
import logging
logger = logging.getLogger(__name__)

from .abstracts import SCPILoad

class BK8616(SCPILoad):
    command_file = "SCPI_BK8616"

    def __init__(self, name, address, connection_type="VISA", **connection_args) -> None:
        super().__init__(name, address, connection_type, **connection_args)
    
    @property
    def enabled(self):
        logger.warning("Output state query not supported for BK8616; returning False.")
        return False

    @enabled.setter
    def enabled(self, value: bool):
        cmd_value = "1" if value else "0"
        self.write("INP", cmd_value) 
    
    @property
    def mode(self):
        logger.warning("Mode query not supported for BK8616; returning empty string.")
        return ""
    
    @mode.setter
    def mode(self, value: str):
        if value.upper() not in {"CURR", "VOLT", "POW", "RES", "IMP"}:
            logger.error(f"Invalid mode '{value}'. Must be one of CURR, VOLT, POW, RES, IMP.")
            return
        self.write("MODE", value.upper())

    @property
    def voltage(self) -> float:
        response = self.query("MEAS:VOLT")
        if response is None:
            logger.error("Failed to read voltage.")
            return 0.0
        try:
            return float(response.strip())
        except ValueError:
            logger.error(f"Unexpected voltage response: {response!r}")
            return 0.0
    
    @voltage.setter
    def voltage(self, value: float):
        self.write("VOLT:ON", value)

    @property
    def current(self) -> float:
        response = self.query("MEAS:CURR")
        if response is None:
            logger.error("Failed to read current.")
            return 0.0
        try:
            return float(response.strip())
        except ValueError:
            logger.error(f"Unexpected current response: {response!r}")
            return 0.0
    
    @current.setter
    def current(self, value: float):
        logger.error("Current set command not supported for BK8616 in this command set.")
    
    @property
    def power(self) -> float:
        response = self.query("MEAS:POW")
        if response is None:
            logger.error("Failed to read power.")
            return 0.0
        try:
            return float(response.strip())
        except ValueError:
            logger.error(f"Unexpected power response: {response!r}")
            return 0.0
    
    @power.setter
    def power(self, value: float):
        self.write("POW", value)
    
