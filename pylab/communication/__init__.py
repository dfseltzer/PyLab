"""
Handles both connections and command sets.  Use the getConnection function to get
the appropriate Connection subclass.

commandset.py defines the CommandSet abstract base class for command set validation.
connection.py defines the Connection abstract base class and Status enum.

connection modules include:
- visa.py : VISA based connections using pyvisa

command set modules include:
- scpi.py : SCPI command sets

"""

from .connection import ConnectionTypes
from .commandset import CommandSetTypes

def getConnection(cnx_type):
    if not ConnectionTypes.is_known(cnx_type):
        raise ValueError(f"Unknown connection type: {cnx_type}")
    
    # Normalize to enum
    if isinstance(cnx_type, str):
        cnx_type = ConnectionTypes[cnx_type]
    
    if cnx_type == ConnectionTypes.VISA:
        from .visa import VISAConnection
        return VISAConnection
    
    raise NotImplementedError(f"Connection type '{cnx_type}' is not implemented.")

def getCommandSet(cmdset_type):
    if not CommandSetTypes.is_known(cmdset_type):
        raise ValueError(f"Unknown command set type: {cmdset_type}")
    
    # Normalize to enum
    if isinstance(cmdset_type, str):
        cmdset_type = CommandSetTypes[cmdset_type]
    
    if cmdset_type == CommandSetTypes.SCPI:
        from .scpi import SCPICommandSet
        return SCPICommandSet
    
    raise NotImplementedError(f"Command set type '{cmdset_type}' is not implemented.")
