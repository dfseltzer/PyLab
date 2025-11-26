"""
Class for making connections easier to get
"""

from enum import Enum

class ConnectionTypes(Enum):
    VISA = 0
    MOCK = 1

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
        from .VISA import VISAConnection
        return VISAConnection
    elif cnx_type == ConnectionTypes.MOCK:
        from .mock import MockConnection
        return MockConnection
    
    raise NotImplementedError(f"Connection type '{cnx_type}' is not implemented.")
