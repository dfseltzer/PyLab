"""
Example script for Keysight N5770A using the mock backend.
"""

import logging
from pylab.devices.keysight import N5770A


def main():
    logging.basicConfig(level=logging.INFO)

    # Use MOCK connection so no hardware is required.
    dev = N5770A("N5770A-MOCK", address=None, connection_type="MOCK")

    # Preload mock responses to illustrate query handling.
    # Order matches the queries below.
    dev._cnx.preload_responses([
        "0",     # initial output state
        "12.34", # measured voltage
        "1.23"   # measured current
    ])

    print("Enabled?", dev.enabled)
    dev.enabled = True
    dev.voltage = 10.0
    dev.current = 1.0

    print("Measured voltage:", dev.voltage)
    print("Measured current:", dev.current)
    print("Commands sent:", dev._cnx.writes)


if __name__ == "__main__":
    main()
