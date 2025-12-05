import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from filter_calculator import calculate_mask_filter, calculate_multiple_masks_filters

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

    def test_multi_filters_perfect(self):
        # Select 0x100 and 0x200. Unselected 0x300.
        # Max filters 2. Should use 2 filters for perfect match.
        selected = [0x100, 0x200]
        unselected = [0x300]
        results, collisions = calculate_multiple_masks_filters(selected, unselected, max_filters=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(len(collisions), 0)
        # Verify masks/filters
        # 1. 0x100 -> Mask 0x7FF, Filter 0x100
        # 2. 0x200 -> Mask 0x7FF, Filter 0x200
        masks = [r[0] for r in results]
        filters = [r[1] for r in results]
        self.assertIn(0x7FF, masks)
        self.assertIn(0x100, filters)
        self.assertIn(0x200, filters)
        
    def test_multi_filters_constrained(self):
        
        selected = [0x100, 0x103]
        unselected = [0x101, 0x102]
        results, collisions = calculate_multiple_masks_filters(selected, unselected, max_filters=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(len(collisions), 2)
        self.assertIn(0x101, collisions)
        self.assertIn(0x102, collisions)
        
    def test_multi_filters_optimized(self):
        selected = [0x100, 0x101, 0x200, 0x201]
        unselected = [0x102, 0x202]
        results, collisions = calculate_multiple_masks_filters(selected, unselected, max_filters=2)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(len(collisions), 0)
        
    def test_multi_filters_forced_split(self):
        
        selected = [0x100, 0x101, 0x200, 0x201]
        unselected = [0x102, 0x202, 0x300]
        results, collisions = calculate_multiple_masks_filters(selected, unselected, max_filters=2)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(len(collisions), 0)

if __name__ == '__main__':
    unittest.main()
