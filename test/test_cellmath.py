import unittest
from pylab.fileio.excel import cellmath

class TestCellMath(unittest.TestCase):
    def test_validate_address_valid(self):
        # Should not raise
        cellmath.validate_address(1, 1)
        cellmath.validate_address(10, 26)

    def test_validate_address_invalid(self):
        with self.assertRaises(ValueError):
            cellmath.validate_address(0, 1)
        with self.assertRaises(ValueError):
            cellmath.validate_address(1, 0)
        with self.assertRaises(ValueError):
            cellmath.validate_address(-1, 1)
        with self.assertRaises(ValueError):
            cellmath.validate_address(1, -1)
        with self.assertRaises(ValueError):
            cellmath.validate_address('A', 1)
        with self.assertRaises(ValueError):
            cellmath.validate_address(1, 'B')

    def test_to_address_single(self):
        self.assertEqual(cellmath.to_address(1, 1), 'A1')
        self.assertEqual(cellmath.to_address(5, 3), 'C5')
        self.assertEqual(cellmath.to_address(10, 27), 'AA10')

    def test_to_address_range(self):
        self.assertEqual(cellmath.to_address(1, 1, 2, 2), 'A1:B2')
        self.assertEqual(cellmath.to_address(3, 4, 5, 6), 'D3:F5')

    def test_from_address_single(self):
        self.assertEqual(cellmath.from_address('A1'), (1, 1))
        self.assertEqual(cellmath.from_address('C5'), (5, 3))
        self.assertEqual(cellmath.from_address('AA10'), (10, 27))

    def test_from_address_range(self):
        self.assertEqual(cellmath.from_address('A1:B2'), (1, 1, 2, 2))
        self.assertEqual(cellmath.from_address('D3:F5'), (3, 4, 5, 6))

    def test_increment_column(self):
        self.assertEqual(cellmath.increment_column('A1', 1), 'B1')
        self.assertEqual(cellmath.increment_column('A1:B2', 2), 'C1:D2')

    def test_increment_row(self):
        self.assertEqual(cellmath.increment_row('A1', 1), 'A2')
        self.assertEqual(cellmath.increment_row('A1:B2', 3), 'A4:B5')

if __name__ == '__main__':
    unittest.main()
