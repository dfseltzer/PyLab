"""
Example script for Keysight N5770A using the mock backend.
"""

import logging
from pylab.devices.keysight import N5770A


def main():
    logging.basicConfig(level=logging.INFO)

    # Use MOCK connection so no hardware is required.
    dev = N5770A("N5770A-MOCK", address=None, connection_type="MOCK")

    print("Enabled?", dev.enabled)
    dev.enabled = True
    dev.voltage = 10.0
    dev.current = 1.0

    print("Measured voltage:", dev.voltage)
    print("Measured current:", dev.current)
    print("Commands sent: (inspect via mock backend if needed)")


if __name__ == "__main__":
    main()
