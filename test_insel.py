import insel
import unittest
import math

class TestBlock(unittest.TestCase):
    def test_pi(self):
        self.assertAlmostEqual(insel.block('pi'), math.pi, places=6) # WTF INSEL? single float precision

    def test_sum(self):
        self.assertAlmostEqual(insel.block('sum', 2), 2, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4), 6, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4, 5), 11, places=8)
    def test_sum(self):
        self.assertAlmostEqual(insel.block('sum', 2), 2, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4), 6, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4, 5), 11, places=8)

class TestTemplate(unittest.TestCase):
    def test_a_times_b(self):
        self.assertAlmostEqual(insel.template('a_times_b'), 9, places=6)
        self.assertAlmostEqual(insel.template('a_times_b', a=4), 12, places=6)
        self.assertAlmostEqual(insel.template('a_times_b', a=4, b=5), 20, places=6)

if __name__ == '__main__':
    unittest.main()

