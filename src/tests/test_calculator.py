import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from filter_calculator import calculate_mask_filter

class TestFilterCalculator(unittest.TestCase):
    def test_single_id(self):
        mask, filter_val = calculate_mask_filter([0x100])
        self.assertEqual(mask, 0x7FF)
        self.assertEqual(filter_val, 0x100)

    def test_two_ids_close(self):
        # 0x100 = 001 0000 0000
        # 0x101 = 001 0000 0001
        # Mask should be 0x7FE (last bit ignored)
        # Filter should be 0x100 (last bit 0)
        mask, filter_val = calculate_mask_filter([0x100, 0x101])
        self.assertEqual(mask, 0x7FE)
        self.assertEqual(filter_val, 0x100)

    def test_two_ids_far(self):
        # 0x100 = 001 0000 0000
        # 0x200 = 010 0000 0000
        # Diff is 0x300 (bits 8 and 9 differ) -> Mask 0x4FF? No.
        # 100 ^ 200 = 011 0000 0000 (0x300)
        # Mask bits 8 and 9 must be 0.
        # Mask = ~0x300 & 0x7FF = 0x4FF
        mask, filter_val = calculate_mask_filter([0x100, 0x200])
        self.assertEqual(mask, 0x4FF)
        self.assertEqual(filter_val & mask, 0x100 & mask)
        self.assertEqual(filter_val & mask, 0x200 & mask)

    def test_empty(self):
        mask, filter_val = calculate_mask_filter([])
        self.assertEqual(mask, 0)
        self.assertEqual(filter_val, 0)

if __name__ == '__main__':
    unittest.main()
