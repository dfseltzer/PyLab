"""
Class for making connections easier to get
"""

from enum import Enum

class ConnectionTypes(Enum):
    VISA = 0

    @staticmethod
    def is_known(val):
        if isinstance(val, ConnectionTypes):
            return True
        if isinstance(val, str):
            return val in ConnectionTypes.__members__
        return False

def getConnection(cnx_type):
    if not ConnectionTypes.is_known(cnx_type):
        raise ValueError(f"Unknown connection type: {cnx_type}")
    
    # Normalize to enum
    if isinstance(cnx_type, str):
        cnx_type = ConnectionTypes[cnx_type]
    
    if cnx_type == ConnectionTypes.VISA:
        from .VISA import VISAConnection # import here, so we don't have to if its not used.
        return VISAConnection
    
    raise NotImplementedError(f"Connection type '{cnx_type}' is not implemented.")