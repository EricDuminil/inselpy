import insel
import unittest
import math
import logging
logging.basicConfig(level=logging.ERROR)

# TODO: ROOT GAIN ATT OFFSET DELAYS 50 inputs


class TestBlock(unittest.TestCase):

    def test_pi(self):
        self.assertAlmostEqual(insel.block('pi'), math.pi, places=6)

    def test_sum(self):
        self.assertAlmostEqual(insel.block('sum', 2), 2, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4), 6, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4, 5), 11, places=8)

    def test_gain(self):
        self.assertAlmostEqual(insel.block('gain',
                                           3, parameters=[2]), 6, places=8)
        self.assertAlmostEqual(insel.block('gain',
                                           1, parameters=[0]), 0, places=8)
        results = insel.block('gain', 2, 5, 7, parameters=[3], outputs=3)
        self.assertIsInstance(results, list,
                              'Gain should return N outputs for N inputs')
        self.assertEqual(len(results), 3,
                         'Gain should return N outputs for N inputs')

    def test_do(self):
        self.assertEqual(len(insel.block('do', parameters=[1, 10, 1])), 10)

    def test_warning_is_fine(self):
        self.assertAlmostEqual(insel.block('acos', 1.5), 0)


class TestTemplate(unittest.TestCase):

    def test_a_times_b(self):
        self.assertAlmostEqual(insel.template('a_times_b'), 9, places=6)
        self.assertAlmostEqual(insel.template('a_times_b', a=4), 12, places=6)
        self.assertAlmostEqual(
            insel.template(
                'a_times_b',
                a=4,
                b=5),
            20,
            places=6)


if __name__ == '__main__':
    unittest.main()
