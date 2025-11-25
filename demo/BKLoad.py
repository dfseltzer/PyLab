from pylab.devices.BKPrecision import BK500B
from pylab import logger
logger.setLevel(10)

dev = BK500B("Eload", None, "VISABlank")

# --- Test: Correctly formatted commands (all from command_set_BK500B.json) ---
try:
    print('Test 1:', dev.write('CURR', 1.5))  # Set current in CC mode (float)
    print('Test 2:', dev.write('VOLT', 12.0))  # Set voltage in CV mode (float)
    print('Test 3:', dev.write('INP', 1))  # Set input on/off state (bool)
    print('Test 4:', dev.write('FUNC', 'CURR'))  # Select input mode (str)
    print('Test 5:', dev.write('LED:CURR', 0.25))  # Set LED rated current (float)
except Exception as e:
    print('Unexpected error in correct command tests:', e)

# --- Test: Incorrectly formatted command (wrong number of arguments) ---
try:
    print('Test 6:', dev.write('CURR'))  # Missing required argument
except Exception as e:
    print('Expected failure for wrong format:', e)
