"""
BK Precision Devices
"""

from .baseclasses import SCPIDevice

class BK500B(SCPIDevice):
    command_file = 'command_set_BK500B'
    def __init__(self, name, address, connection_type="VISA", **connection_args) -> None:
        super().__init__(name, address, self.command_file, 
                         connection_type, **connection_args)
        
    