import unittest
import math


class CustomAssertions(unittest.TestCase):
    def assertNaN(self, x):
        self.assertTrue(math.isnan(x), f'{x} should be NaN')

    def assertNotNaN(self, x):
        self.assertFalse(math.isnan(x), f'{x} should not be NaN')

    def assertInf(self, x):
        self.assertTrue(math.isinf(x), f'{x} should be Infinity')

    def compareLists(self, list1, expected, places=8):
        self.assertIsInstance(list1, list)
        self.assertTrue(hasattr(expected, '__iter__'))
        list2 = list(expected)
        self.assertEqual(len(list1), len(list2),
                         "Both lists should have the same length.")
        for a, b in zip(list1, list2):
            self.assertAlmostEqual(a, b, places=places)
