"""
Automate a simple source/load sweep and record measurements to Excel.

This demo uses mock connections by default. Replace connection_type="MOCK"
with your actual connection type (e.g., "VISA") and real addresses.
"""

import datetime
import time

from pylab.devices import N5770A
from pylab.devices import BK8616
from pylab.fileio.excel import Workbook

# Create devices (using MOCK backends for offline demo)
source = N5770A("Source", address=None, connection_type="MOCK")
load = BK8616("Load", address=None, connection_type="MOCK")

# Define test points (voltage, current) and dwell time seconds
test_points = [
    (5.0, 0.5),
    (10.0, 1.0),
    (12.0, 1.5),
]
dwell = 2  # seconds between steps

# Prepare Excel workbook and sheet
sheet_name = datetime.datetime.now().strftime("%Y%m%d")
print(sheet_name, type(sheet_name))
wb = Workbook("TestDemo.xlsx",
                increment_col=0, # after each write, increment cols by this. Default is 0
                increment_row=1, # after each write, increment rows by this. Default is 0
                open_now=True) # Open workbook immediately
wb.add_sheet(sheet_name) # add new sheet and select it
headers = [
    "Step",
    "Src_V_Set",
    "Src_I_Set",
    "Src_V_Meas",
    "Src_I_Meas",
    "Load_V_Meas",
    "Load_I_Meas",
    "Timestamp",
]
nextaddress = wb.write_range(((1, 1), (1, len(headers))), [headers])

# Run sequence
for idx, (v_set, i_set) in enumerate(test_points, start=1):
    # Set source setpoints
    source.voltage = v_set
    source.current = i_set
    # Enable source/output (mock does not actually enforce)
    source.enabled = True
    load.enabled = True

    time.sleep(dwell)

    # Measure
    src_v = source.voltage
    src_i = source.current
    load_v = load.voltage
    load_i = load.current
    timestamp = datetime.datetime.now().isoformat()

    nextaddress = wb.write_range(nextaddress,[[idx, v_set, i_set, src_v, src_i, load_v, load_i, timestamp]])

# Save and close workbook
wb.save()
wb.close()
print(f"Recorded {len(test_points)} steps to TestDemo.xlsx sheet {sheet_name}")
