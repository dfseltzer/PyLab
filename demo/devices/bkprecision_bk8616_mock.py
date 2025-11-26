"""
Example script for BK Precision 8616 using the mock backend.
"""

import logging
from pylab.devices.BKPrecision import BK8616


def main():
    logging.basicConfig(level=logging.INFO)

    dev = BK8616("BK8616-MOCK", address=None, connection_type="MOCK")

    # Toggle output and set values (validation only; MOCK just records writes)
    dev.enabled = True
    dev.mode = "CURR"
    dev.voltage = 5.0
    dev.current = 0.5
    dev.power = 2.5

    print("Voltage read:", dev.voltage)
    print("Current read:", dev.current)
    print("Power read:", dev.power)
    print("Commands sent: (inspect via mock backend if needed)")


if __name__ == "__main__":
    main()
