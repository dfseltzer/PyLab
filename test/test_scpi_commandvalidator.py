import unittest
from pylab.communication.SCPI import CommandValidator

# Example command set for testing
EXAMPLE_COMMANDS = {
    'INP:SHOR': {
        'arguments': [
            {'type': 'bool', 'required': True, 'default': None}
        ],
        'help': 'Set short circuit function state (0/OFF or 1/ON)'
    },
    'INP:SHOR?': {
        'arguments': [],
        'response': [
            {'type': 'bool'}
        ],
        'help': 'Query short circuit function state (returns 0/OFF or 1/ON)'
    },
    'SOUR:FUNC': {
        'arguments': [
            {'type': 'str', 'values': ['VOLT', 'CURR', 'POW', 'RES', 'DYN', 'LED', 'IMP'], 'required': True, 'default': None}
        ],
        'help': 'Set source function mode'
    },
    'SOUR:FUNC?': {
        'arguments': [],
        'response': [
            {'type': 'str', 'values': ['VOLT', 'CURR', 'POW', 'RES', 'DYN', 'LED', 'IMP']}
        ],
        'help': 'Query source function mode'
    },
    'VOLT': {
        'arguments': [
            {'type': 'int', 'required': False, 'default': 1, 'range': [1, 4], 'suffix': True},
            {'type': 'float', 'required': True, 'default': None, 'range': [0, 60]}
        ],
        'numeric_suffix': True,
        'suffix_argument': 0,
        'help': 'Set voltage for a given channel (e.g., VOLT1 12.0)'
    },
    'VOLT?': {
        'arguments': [
            {'type': 'int', 'required': False, 'default': 1, 'range': [1, 4], 'suffix': True}
        ],
        'numeric_suffix': True,
        'suffix_argument': 0,
        'response': [
            {'type': 'float'}
        ],
        'help': 'Query voltage for a given channel (e.g., VOLT1?)'
    },
    'DYN:SEQ': {
        'arguments': [
            {'type': 'float', 'required': True, 'default': None, 'variadic': True}
        ],
        'help': 'Set dynamic sequence with variable number of steps (DYN:SEQ 1.0,2.0,3.0,...)'
    },
    'MEAS:VOLT?': {
        'arguments': [],
        'response': [
            {'type': 'float'}
        ],
        'help': 'Query the average DC voltage at the load input'
    }
}

class TestCommandValidator(unittest.TestCase):
    def setUp(self):
        self.cv = CommandValidator(EXAMPLE_COMMANDS)

    def test_write_string_bool(self):
        self.assertEqual(self.cv.write_string('INP:SHOR', 1), 'INP:SHOR 1')
        self.assertEqual(self.cv.write_string('INP:SHOR', 'ON'), 'INP:SHOR ON')
        with self.assertRaises(TypeError):
            self.cv.write_string('INP:SHOR', 'INVALID')

    def test_write_string_enum(self):
        self.assertEqual(self.cv.write_string('SOUR:FUNC', 'VOLT'), 'SOUR:FUNC VOLT')
        with self.assertRaises(ValueError):
            self.cv.write_string('SOUR:FUNC', 'BADMODE')

    def test_write_string_numeric_suffix(self):
        self.assertEqual(self.cv.write_string('VOLT', 2, 12.5), 'VOLT2 12.5')
        self.assertEqual(self.cv.write_string('VOLT', 1, 5.0), 'VOLT1 5.0')
        # Use default suffix
        self.assertEqual(self.cv.write_string('VOLT', 12.0), 'VOLT1 12.0')
        with self.assertRaises(ValueError):
            self.cv.write_string('VOLT')  # Missing required float argument
        with self.assertRaises(TypeError):
            self.cv.write_string('VOLT', 2, 'badfloat')

    def test_write_string_variadic(self):
        self.assertEqual(self.cv.write_string('DYN:SEQ', 1.0), 'DYN:SEQ 1.0')
        self.assertEqual(self.cv.write_string('DYN:SEQ', 1.0, 2.0, 3.0), 'DYN:SEQ 1.0,2.0,3.0')
        with self.assertRaises(TypeError):
            self.cv.write_string('DYN:SEQ', 'bad')

    def test_query_string(self):
        self.assertEqual(self.cv.query_string('VOLT', 2), 'VOLT2?')
        self.assertEqual(self.cv.query_string('VOLT'), 'VOLT1?')
        self.assertEqual(self.cv.query_string('MEAS:VOLT?'), 'MEAS:VOLT?')

    def test_parse_responce_bool(self):
        self.assertTrue(self.cv.parse_responce('INP:SHOR?', 'ON'))
        self.assertFalse(self.cv.parse_responce('INP:SHOR?', 'OFF'))
        self.assertTrue(self.cv.parse_responce('INP:SHOR?', 1))
        self.assertFalse(self.cv.parse_responce('INP:SHOR?', 0))

    def test_parse_responce_enum(self):
        self.assertEqual(self.cv.parse_responce('SOUR:FUNC?', 'VOLT'), 'VOLT')
        with self.assertRaises(ValueError):
            self.cv.parse_responce('SOUR:FUNC?', 'BADMODE')

    def test_parse_responce_numeric(self):
        self.assertEqual(self.cv.parse_responce('VOLT?', 12.5), 12.5)
        self.assertEqual(self.cv.parse_responce('MEAS:VOLT?', '5.0'), 5.0)

    def test_parse_responce_multi(self):
        # Add a multi-response command for this test
        multi_cmds = dict(EXAMPLE_COMMANDS)
        multi_cmds['MULTI?'] = {
            'arguments': [],
            'response': [
                {'type': 'int'},
                {'type': 'float'},
                {'type': 'str', 'values': ['A', 'B']}
            ]
        }
        cv2 = CommandValidator(multi_cmds)
        self.assertEqual(cv2.parse_responce('MULTI?', '1,2.5,A'), [1, 2.5, 'A'])
        with self.assertRaises(ValueError):
            cv2.parse_responce('MULTI?', '1,2.5,X')
        with self.assertRaises(ValueError):
            cv2.parse_responce('MULTI?', '1,2.5')

if __name__ == '__main__':
    unittest.main()
