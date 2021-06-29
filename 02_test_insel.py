# coding=utf8
import unittest
import math
import logging
import insel
import tempfile
from pathlib import Path
logging.basicConfig(level=logging.ERROR)

# INSEL 8.3 convention
STUTTGART = [48.77, 9.18, 1]

class CustomAssertions(unittest.TestCase):
    def assertNaN(self, x):
        self.assertTrue(math.isnan(x), f'{x} should be NaN')

    def assertInf(self, x):
        self.assertTrue(math.isinf(x), f'{x} should be Infinity')

    def compareLists(self, list1, expected, places=8):
        self.assertIsInstance(list1, list)
        self.assertTrue(hasattr(expected,'__iter__'))
        list2 = list(expected)
        self.assertEqual(len(list1), len(list2),
                         "Both lists should have the same length.")
        for a, b in zip(list1, list2):
            self.assertAlmostEqual(a, b, places=places)

class TestBlock(CustomAssertions):
    def test_pi(self):
        self.assertAlmostEqual(insel.block('pi'), math.pi, places=6)

    def test_sum(self):
        self.assertAlmostEqual(insel.block('sum', 2), 2, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4), 6, places=8)
        self.assertAlmostEqual(insel.block('sum', 2, 4, 5), 11, places=8)
        self.assertNaN(insel.block('sum', 2, float('nan')))
        self.assertInf(insel.block('sum', 2, float('inf')))

    def test_if(self):
        self.assertAlmostEqual(insel.block('if', 3.14, 1), 3.14, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, 2), 3.14, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, 0.5), 3.14, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, -0.5), 3.14, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, float('inf')), 3.14, places=6)
        #  Weird, actually. It should be empty. Seems to require a DO block
        self.assertAlmostEqual(insel.block('if', 3.14, 0), 0.0, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, 0.4), 0.0, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, -0.4), 0.0, places=6)
        self.assertNaN(insel.block('if', float('nan'), 1))
        self.assertAlmostEqual(insel.block('if', 3.14, float('nan')), 0.0, places=6)

    def test_ifelsenan(self):
        self.assertAlmostEqual(insel.block('ifelsenan', 3.14, 1), 3.14, places=6)
        self.assertAlmostEqual(insel.block('ifelsenan', 3.14, 2), 3.14, places=6)
        self.assertAlmostEqual(insel.block('ifelsenan', 3.14, 0.5), 3.14, places=6)
        self.assertAlmostEqual(insel.block('ifelsenan', 3.14, -0.5), 3.14, places=6)
        self.assertAlmostEqual(insel.block('ifelsenan', 3.14, float('inf')), 3.14, places=6)
        self.assertNaN(insel.block('ifelsenan', 3.14, 0))
        self.assertNaN(insel.block('ifelsenan', 3.14, 0.4))
        self.assertNaN(insel.block('ifelsenan', 3.14, -0.4))
        self.assertNaN(insel.block('ifelsenan', 3.14, float('nan')))

    def test_ifpos(self):
        self.assertAlmostEqual(insel.block('ifpos', 3.14), 3.14, places=6)
        #  Weird, actually. It should be empty. Seems to require a DO block
        self.assertAlmostEqual(insel.block('ifpos', -3.14), 0.0, places=6)

    def test_ifneg(self):
        self.assertAlmostEqual(insel.block('ifneg', -3.14), -3.14, places=6)
        #  Weird, actually. It should be empty. Seems to require a DO block
        self.assertAlmostEqual(insel.block('ifneg', 3.14), 0.0, places=6)

    def test_diff(self):
        self.assertAlmostEqual(insel.block('diff', 4, 1), 3, places=8)
        self.assertAlmostEqual(insel.block('diff', 1, 4), -3, places=8)
        self.assertAlmostEqual(insel.block('diff', 1000, 1), 999, places=8)
        self.assertAlmostEqual(insel.block('diff', 500, 123), 377, places=8)

        self.assertNaN(insel.block('diff', 2, float('nan')))
        self.assertInf(insel.block('diff', 2, float('inf')))

        # Not exactly 2 inputs:
        self.assertRaises(Exception, insel.block, 'diff')
        self.assertRaises(Exception, insel.block, 'diff', 1)
        self.assertRaises(Exception, insel.block, 'diff', 1, 2, 3)

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
            len(insel.block('gain', *range(10),
                            parameters=[5], outputs=10)),
            10, '10 inputs should be enough for GAIN')

    def test_att(self):
        self.assertAlmostEqual(insel.block('att',
                                           3, parameters=[2]), 1.5, places=8)
        # Division by 0
        self.assertRaises(Exception, insel.block, 'att', 1, parameters=[0])
        # Multiple inputs
        results = insel.block('att', 9, 3, 6, 7.5, parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[3.0, 1.0, 2.0, 2.5]')

    def test_div(self):
        self.assertAlmostEqual(insel.block('div',
                                           3, 2), 1.5, places=8)
        # Division by 0
        m = insel.OneBlockModel('div', inputs=[2, 0])
        m.run()
        self.assertTrue(len(m.warnings) >= 1, "A warning should be shown")

    def test_offset(self):
        self.assertAlmostEqual(insel.block('offset',
                                           3, parameters=[-2]), 1.0, places=8)
        # Multiple inputs
        results = insel.block('offset', 9, 3, 6, -10.5,
                              parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[12.0, 6.0, 9.0, -7.5]')

    def test_root(self):
        self.assertAlmostEqual(insel.block('root', 2,
                                           parameters=[2]), 2**0.5, places=6)
        self.assertEqual(repr(insel.block('root', 9, 16, 25, parameters=[2], outputs=3)),
                         '[3.0, 4.0, 5.0]')

    def test_sqrt(self):
        self.assertAlmostEqual(insel.block('sqrt', 2), 2**0.5, places=6)
        self.assertEqual(repr(insel.block('sqrt', 9, 16, 25, outputs=3)),
                         '[3.0, 4.0, 5.0]')

    def test_abs(self):
        self.assertAlmostEqual(insel.block('abs', 1.23), 1.23, places=6)
        self.assertAlmostEqual(insel.block('abs', -1.23), 1.23, places=6)
        self.assertEqual(repr(insel.block('abs', -9, 16, -25, outputs=3)),
                         '[9.0, 16.0, 25.0]')

    def test_exp(self):
        self.assertAlmostEqual(insel.block('exp', 1.0), 2.71828, places=5)
        self.assertAlmostEqual(insel.block('exp', 0.0), 1.0, places=6)
        self.assertAlmostEqual(insel.block('exp', -1.0), 1 / 2.71828, places=6)
        self.assertAlmostEqual(insel.block('exp', 20), math.exp(20), places=-2)
        self.assertEqual(' '.join(['%.2f' % x for x in
                                   insel.block('exp', -3.5, -2.0, 1.4, 2.6, 4.7, outputs=5)]),
                         '0.03 0.14 4.06 13.46 109.95')

    def test_nop(self):
        self.assertAlmostEqual(insel.block('nop', 1.0), 1.0, places=5)
        self.assertAlmostEqual(insel.block('nop', 0.0), 0.0, places=6)
        self.assertAlmostEqual(insel.block('nop', -1.0), -1.0, places=6)
        self.assertAlmostEqual(insel.block('nop', 20), 20, places=5)
        self.assertEqual(' '.join(['%.2f' % x for x in
                                   insel.block('nop', -3.5, -2.0, 1.4, 2.6, 4.7, outputs=5)]),
                         '-3.50 -2.00 1.40 2.60 4.70')

    def test_chs(self):
        self.assertAlmostEqual(insel.block('chs', 1.0), -1.0, places=5)
        self.assertAlmostEqual(insel.block('chs', 1.23), -1.23, places=5)
        self.assertAlmostEqual(insel.block('chs', -234.56), 234.56, places=5)
        self.assertEqual(' '.join(['%.2f' % x for x in
                                   insel.block('chs', 3.5, 2.0, -1.4, -2.6, -4.7, outputs=5)]),
                         '-3.50 -2.00 1.40 2.60 4.70')

    def test_int(self):
        self.assertAlmostEqual(insel.block('int', 10.0), 10.0, places=5)
        self.assertAlmostEqual(insel.block('int', 1.23), 1.0, places=5)
        self.assertAlmostEqual(insel.block('int', 1.67), 1.0, places=5)
        self.assertAlmostEqual(insel.block('int', -1.3), -1.0, places=5)
        self.assertAlmostEqual(insel.block('int', -1.7), -1.0, places=5)
        self.assertEqual(repr(insel.block('int', -9.7, 16.2, -25.7, outputs=3)),
                         '[-9.0, 16.0, -25.0]')

    def test_anint(self):
        self.assertAlmostEqual(insel.block('anint', 10.0), 10.0, places=5)
        self.assertAlmostEqual(insel.block('anint', 1.23), 1.0, places=5)
        self.assertAlmostEqual(insel.block('anint', 1.67), 2.0, places=5)
        self.assertAlmostEqual(insel.block('anint', -1.3), -1.0, places=5)
        self.assertAlmostEqual(insel.block('anint', -1.7), -2.0, places=5)
        self.assertEqual(repr(insel.block('anint', -9.7, 16.2, -25.7, outputs=3)),
                         '[-10.0, 16.0, -26.0]')

    def test_frac(self):
        self.assertAlmostEqual(insel.block('frac', 10.0), 0.0, places=5)
        self.assertAlmostEqual(insel.block('frac', 1.23), 0.23, places=5)
        self.assertAlmostEqual(insel.block('frac', 1.67), 0.67, places=5)
        self.assertAlmostEqual(insel.block('frac', -1.3), -0.3, places=5)
        self.assertAlmostEqual(insel.block('frac', -1.7), -0.7, places=5)
        self.assertEqual(' '.join(['%.1f' % x for x in
                                   insel.block('frac', 3.5, 2.0, -1.4, -2.6, -4.7, outputs=5)]),
                         '0.5 0.0 -0.4 -0.6 -0.7')

    def test_mtm(self):
        december = insel.block('mtm2', 12, parameters=['Strasbourg'], outputs=9)
        # 1.5° in december in Strasbourg
        self.assertAlmostEqual(december[2], 1.5, places=1)
        # ~28W/m² in december in Strasbourg
        self.assertAlmostEqual(december[0], 28, places=0)
        july = insel.block('mtm2', 7, parameters=['Stuttgart'], outputs=9)
        # 19° in july in Stuttgart
        self.assertAlmostEqual(july[2], 19, places=0)
        # ~230W/m² in july in Stuttgart
        self.assertAlmostEqual(july[0], 230, places=-1)


    def test_mtmlalo(self):
        m = insel.OneBlockModel('MTMLALO', inputs=[5], parameters=STUTTGART)
        m.run()
        self.assertTrue(len(m.warnings) >= 1, "A warning should be shown")
        self.assertTrue("Block 00002: '48.77° N, 9.18° W' seems to be in the ocean" in str(m.warnings))
        self.assertTrue("MTMLALO is deprecated" in str(m.warnings))

        m = insel.OneBlockModel('MTMLALO2', inputs=[6], parameters=STUTTGART)
        r = m.run()
        self.assertEqual(m.warnings, [], 'No problem with correct convention')
        # ~225W/m² in june in Stuttgart
        self.assertAlmostEqual(r, 225, places=0)

    def test_moonae(self):
        # Tested with Stellarium
        moon_stuttgart = insel.block('MOONAE2',
                                     2021, 2, 18, 23, 33,
                                     parameters=STUTTGART, outputs=2)
        self.compareLists(moon_stuttgart, [279, 13], places=0)
        moon_stuttgart = insel.block('MOONAE2',
                                     2021, 2, 23, 5, 7, 30,
                                     parameters=STUTTGART, outputs=2)
        self.compareLists(moon_stuttgart, [308.5, 0], places=0)
        # Tested with http://www.stjarnhimlen.se/comp/tutorial.html#9
        moon_sweden = insel.block('MOONAE2',
                                  1990, 4, 19, 2,
                                  parameters=[60, 15, 2], outputs=5)
        self.compareLists(moon_sweden,
                          [101 + 46.0 / 60, -16 - 11.0 / 60, -19.9, 272.3 - 0.5, 100], places=0)

        moon_stuttgart = insel.block('MOONAE2',
                                     2021, 5, 26, 13, 13,
                                     parameters=STUTTGART, outputs=5)
        self.assertTrue(moon_stuttgart[4] < 2.0,
                        "26.05.2021 should be a full moon.")

        moon_stuttgart = insel.block('MOONAE2',
                                     2021, 6, 10, 12, 0,
                                     parameters=STUTTGART, outputs=5)
        self.assertTrue(moon_stuttgart[4] > 178,
                        "10.06.2021 should be a new moon.")

    def test_do(self):
        self.assertEqual(len(insel.block('do', parameters=[1, 10, 1])), 10)
        many_points = insel.block('do', parameters=[-10, 10, 0.1])
        self.compareLists(many_points, [x / 10.0 for x in range(-100, 101)],
                          places=5)

    def test_warning_is_fine(self):
        self.assertAlmostEqual(insel.block('acos', 1.5), 0)

    def test_nan(self):
        self.assertNaN(insel.block('nan'))

    def test_infinity(self):
        self.assertTrue(math.isinf(insel.block('infinity')))
        self.assertAlmostEqual(float('+inf'), insel.block('infinity'))

class TestTemplate(CustomAssertions):
    def test_empty_if(self):
        self.assertEqual(insel.template('empty_if'), [])

    def test_ifelsenan(self):
        odds_as_nans = insel.template('odds_as_nans')
        self.compareLists(odds_as_nans[::2], range(-10, 12, 2))
        for odd in odds_as_nans[1::2]:
            self.assertNaN(odd)

    def test_if(self):
        only_evens = insel.template('remove_odds')
        self.compareLists(only_evens, range(-10, 12, 2))

    def test_aligned_screen_block(self):
        # Numbers should not be too close to each other
        matrix = insel.template('expg')
        for x, row in zip(range(-14, 19), matrix):
            x = x / 2
            self.assertAlmostEqual(x, row[0], places=6)
            self.assertAlmostEqual(r1 := 10**x, row[1], delta=r1/1e6)
            self.assertAlmostEqual(r2 := -10**(-x), row[2], delta=-r2/1e6)

    def test_updated_coordinates(self):
        v1_results = insel.template('nurnberg_v1',
                                    latitude=49.5,
                                    old_longitude=-11.08,
                                    old_timezone=23
                                    )
        v2_results = insel.template('nurnberg_v2',
                                    latitude=49.5,
                                    longitude=11.08,
                                    timezone=+1
                                    )
        self.compareLists(v1_results, [3865, 3645], places=-1)
        self.compareLists(v2_results, v1_results, places=3)

    def test_a_times_b(self):
        self.assertAlmostEqual(insel.template('a_times_b'), 9, places=6)
        self.assertAlmostEqual(insel.template('a_times_b', a=4), 12, places=6)
        self.assertAlmostEqual(insel.template('a_times_b', a=4, b=5),
                               20, places=6)



    def test_non_ascii_template(self):
        utf8_template = insel.Template('a_times_b_utf8', a=2, b=2)
        utf8_template.timeout = 5
        self.assertAlmostEqual(utf8_template.run(), 4, places=6)

        iso_template = insel.Template('a_times_b_iso8859', a=4, b=4)
        iso_template.timeout = 5
        self.assertAlmostEqual(iso_template.run(), 16, places=6)

    def test_sunpower_isc(self):
        spr_isc = insel.template('i_sc', pv_id='008823', temperature=25, irradiance=1000)
        self.assertIsInstance(spr_isc, float)
        self.assertAlmostEqual(spr_isc, 5.87, places=2)

    def test_write_block(self):
        self.run_write_block()
        self.run_write_block(overwrite=0)
        self.run_write_block(overwrite=1)
        self.run_write_block(overwrite=2)

        self.run_write_block(basename='Ñüößç&txt.täxt€',
                             header='#ßeäöütµ§%&²³@°')

        self.run_write_block(fortran_format='(F10.5)')

        self.run_write_block(overwrite=0, fnq=0)
        self.run_write_block(overwrite=0, fnq=1)

        self.run_write_block(overwrite=0, fnq=0, separator=0)
        self.run_write_block(overwrite=0, fnq=0, separator=1)
        self.run_write_block(overwrite=0, fnq=0, separator=2)

        self.run_write_block(header='#Some header here')

    def run_write_block(self, basename='test.dat', **write_params):
        separator = [None, ',', ';'][write_params.get('separator', 0)]
        with tempfile.TemporaryDirectory() as tmpdirname:
            dat_file = Path(tmpdirname) / basename
            self.assertFalse(dat_file.exists())
            model = insel.Template('write_params', dat_file=dat_file, **write_params)
            model.run()
            self.assertEqual(model.warnings, [])
            self.assertTrue(dat_file.exists(), "File should have been written")
            with open(dat_file) as out:
                if write_params.get('header'):
                    next(out)
                content = out.readlines()
                written = [float(line.split(separator)[0]) for line in content]
                self.compareLists(written, range(1, 11), places=5)

if __name__ == '__main__':
    unittest.main(exit=False)
    print(f'Total INSEL calls : {insel.insel.Insel.calls}')
