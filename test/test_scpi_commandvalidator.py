import unittest
from unittest.mock import patch

from pylab.communication.SCPI import CommandValidator


DEVICE_COMMANDS = {
    "INP:SHOR": {
        "set": [{"type": "bool", "required": True, "default": None}],
        "query": [],
        "help": "Short circuit function state",
        "response": [{"type": "bool"}],
    },
    "FUNC": {
        "set": [{"type": "str", "required": True, "values": ["VOLT", "CURR"]}],
        "query": None,
        "help": "Select input mode",
        "response": None,
    },
    "POW": {
        "set": [{"type": "float", "required": True, "default": None}],
        "query": None,
        "help": "Power setpoint",
        "response": None,
    },
    "VOLT1": {
        "set": [{"type": "float", "required": True, "default": None, "range": [0, 60]}],
        "query": [],
        "help": "Set/query voltage for channel 1",
        "response": [{"type": "float"}],
    },
    "DYN:SEQ": {
        "set": [{"type": "float", "required": True, "default": None, "variadic": True}],
        "query": None,
        "help": "Dynamic sequence",
        "response": None,
    },
}

COMMON_COMMANDS = {
    "MEAS:VOLT": {
        "set": None,
        "query": [],
        "help": "Measure voltage",
        "response": [{"type": "float"}],
    }
}


class TestCommandValidator(unittest.TestCase):
    def setUp(self):
        self.patcher = patch(
            "pylab.communication.SCPI.load_data_file",
            side_effect=lambda fname: {
                "SCPI_Common.json": {"commands": COMMON_COMMANDS},
                "TEST": {"commands": DEVICE_COMMANDS},
            }[fname],
        )
        self.mock_loader = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.cv = CommandValidator("TEST")

    def test_set_command_builds_string(self):
        self.assertEqual(self.cv("INP:SHOR", "ON"), "INP:SHOR ON")
        with self.assertRaises(TypeError):
            self.cv("INP:SHOR", "INVALID")

    def test_query_command_builds_string(self):
        self.assertEqual(self.cv("INP:SHOR?"), "INP:SHOR?")
        self.assertEqual(self.cv("MEAS:VOLT?"), "MEAS:VOLT?")

    def test_arg_count_and_range(self):
        with self.assertRaises(ValueError):
            self.cv("VOLT1")  # missing required float
        with self.assertRaises(ValueError):
            self.cv("VOLT1", 100.0)  # out of range
        self.assertEqual(self.cv("VOLT1", 12.5), "VOLT1 12.5")

    def test_variadic(self):
        self.assertEqual(self.cv("DYN:SEQ", 1.0), "DYN:SEQ 1.0")
        self.assertEqual(self.cv("DYN:SEQ", 1.0, 2.0, 3.0), "DYN:SEQ 1.0,2.0,3.0")
        with self.assertRaises(TypeError):
            self.cv("DYN:SEQ", "bad")

    def test_query_not_supported(self):
        with self.assertRaises(KeyError):
            self.cv("FUNC?")
        with self.assertRaises(KeyError):
            self.cv("POW?")

    def test_unknown_command(self):
        with self.assertRaises(KeyError):
            self.cv("UNKNOWN")


if __name__ == "__main__":
    unittest.main()
