# PyLab
Python lab equipment scripting library

## Installation
A VISA backend is needed.  Currently development is being done with these items... 
- pyvisa-py: python based VISA implementation
- psutil: to help with TCPIP:instr resource discovery
- zeroconf: to help with TCPIP:hislip resource discovery

## SCPI JSON Validation

Validate SCPI command set files against the shared schema:

```bash
python -m pylab.cli.validate_scpi               # validate all pylab/data/*.json
python -m pylab.cli.validate_scpi pylab/data/SCPI_N5770A.json  # validate specific file(s)
```
