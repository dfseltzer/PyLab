
import sys
from typing import Optional

class PyWin32NotInstalledError(ImportError):
    """Raised when pywin32 is not installed or not properly configured."""
    
    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = (
                "pywin32 is required but not installed or not properly configured.\n\n"
                "To install pywin32, run:\n"
                "    pip install pywin32\n\n"
                "After installation, you may need to run the post-install script:\n"
                "    python Scripts/pywin32_postinstall.py -install\n\n"
                "Note: pywin32 only works on Windows systems."
            )
        super().__init__(message)

if sys.platform != "win32":
        raise PyWin32NotInstalledError(
            "This package requires Windows to interact with Excel via pywin32.\n"
            f"Current platform: {sys.platform}")

try:
    import win32com.client
    import pywintypes
except ImportError as e:
    raise PyWin32NotInstalledError() from e

try:
    # Test with a simple COM object
    win32com.client.Dispatch("Scripting.Dictionary")
except Exception as e:
    raise PyWin32NotInstalledError(
        "pywin32 is installed but may not be properly configured.\n\n"
        "Try running the post-install script:\n"
        "    python Scripts/pywin32_postinstall.py -install\n\n"
        f"Error details: {str(e)}") from e
