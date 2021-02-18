import insel
import unittest
import math
import logging
logging.basicConfig(level=logging.ERROR)


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
        self.assertEqual(repr(results), '[6.0, 15.0, 21.0]')
        self.assertEqual(
            len(insel.block('gain', *list(range(50)), parameters=[5], outputs=50)), 50, '50 inputs should be enough for GAIN')

    def test_att(self):
        self.assertAlmostEqual(insel.block('att',
                                           3, parameters=[2]), 1.5, places=8)
        # Division by 0
        self.assertRaises(Exception, insel.block, 'att', 1, parameters=[0])
        # Multiple inputs
        results = insel.block('att', 9, 3, 6, 7.5, parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[3.0, 1.0, 2.0, 2.5]')

    def test_offset(self):
        self.assertAlmostEqual(insel.block('offset',
                                           3, parameters=[-2]), 1.0, places=8)
        # Multiple inputs
        results = insel.block('offset', 9, 3, 6, -10.5,
                              parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[12.0, 6.0, 9.0, -7.5]')

    def test_root(self):
        self.assertAlmostEqual(insel.block('root', 2,
                                           parameters=[2]), 1.4142135, places=6)
        self.assertEqual(repr(insel.block('root', 9, 16, 25, parameters=[2], outputs=3)),
                         '[3.0, 4.0, 5.0]')

    def test_mtm(self):
        december = insel.block('mtm', 12, parameters=['Strasbourg'], outputs=9)
        # 1.5° in december in Strasbourg
        self.assertAlmostEqual(december[2], 1.5, places=1)
        # ~28W/m² in december in Strasbourg
        self.assertAlmostEqual(december[0], 28, places=0)
        july = insel.block('mtm', 7, parameters=['Stuttgart'], outputs=9)
        # 19° in july in Stuttgart
        self.assertAlmostEqual(july[2], 19, places=0)
        # ~230W/m² in july in Stuttgart
        self.assertAlmostEqual(july[0], 230, places=-1)

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
