"""
Demo of the CommandSet.help method using the BK8616 SCPI command set.
Shows a broad regex search and then a narrowed single-match lookup.
"""

import logging

from pylab.communication.scpi import SCPICommandSet

logging.basicConfig(level=logging.INFO, format="%(message)s")

cmdset = SCPICommandSet("SCPI_BK8616")

print("=== Broad search with regex 'MEAS' ===")
cmdset.help("MEAS")

print("\n=== Narrow search with regex 'MEAS:VOLT:M.*' ===")
cmdset.help(r"MEAS:VOLT:M.*")

print("\n=== Single command help, 'MEAS:VOLT:MAX' ===")
cmdset.help(r"MEAS:VOLT:MAX")

print("\n=== Single command help, 'MEAS:VOLT:MAX' ===")
cmdset.help("INP$")