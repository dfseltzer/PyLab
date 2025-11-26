"""
Example script for BK Precision 8616 using the mock backend.
"""

import logging
from pylab.devices.BKPrecision import BK8616


def main():
    logging.basicConfig(level=logging.INFO)

    dev = BK8616("BK8616-MOCK", address=None, connection_type="MOCK")

    # Preload mock responses for queries: enabled, meas:volt, meas:curr, meas:pow
    dev._cnx.preload_responses([
        "1",     # enabled? (though getter currently returns False; still safe)
        "5.0",   # voltage
        "0.5",   # current
        "2.5"    # power
    ])

    # Toggle output and set values (validation only; MOCK just records writes)
    dev.enabled = True
    dev.mode = "CURR"
    dev.voltage = 5.0
    dev.current = 0.5
    dev.power = 2.5

    print("Voltage read:", dev.voltage)
    print("Current read:", dev.current)
    print("Power read:", dev.power)
    print("Commands sent:", dev._cnx.writes)


if __name__ == "__main__":
    main()
