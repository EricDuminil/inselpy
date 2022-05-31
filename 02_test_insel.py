# coding=utf8
import unittest
import math
import logging
import tempfile
import os
from pathlib import Path
import contextlib
from datetime import datetime, timedelta
from collections import Counter
from calendar import monthrange
from typing import List
import insel
from insel.insel import Insel, InselError

logging.basicConfig(level=logging.ERROR)

SCRIPT_DIR = Path(__file__).resolve().parent

# TODO: Test with LC_ALL = DE
# TODO: Test if insel_gui is installed?
# TODO: Add gnuplot tests


@contextlib.contextmanager
def cwd(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


# INSEL 8.3 convention
STUTTGART = [48.77, 9.18, 1]  # type: List[insel.Parameter]


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


class TestBlock(CustomAssertions):
    def test_blocks_are_unique(self):
        insel_b = insel.raw_run('-b')
        blocks = Counter(insel_b.split('\n\n')[-1].split())
        self.assertTrue(len(blocks) > 300, "There should be many blocks")
        duplicates = [(b, c) for (b, c) in blocks.most_common() if c > 1]
        if duplicates:
            self.fail("Some blocks are defined multiples times : " +
                      ','.join(f"{b} ({c} times)" for (b, c) in duplicates))

    def test_blocks_have_been_deleted(self):
        """
        Some blocks were just too confusing or broken,
        and should not be available anymore.
        """
        insel_b = insel.raw_run('-b')
        blocks = set(insel_b.split('\n\n')[-1].split())
        deleted_blocks = ['DRY', 'FURWALL', 'FURWALL2', 'GASIF',
                          'GENBOD', 'GOMPERTZ', 'HEATEX', 'MIXING', 'OPTIM',
                          'PRIMARY', 'SECON1', 'SECON2', 'TIMEMS', 'TIMEMS0',
                          'DIV2', 'NOW0', 'EPLUS', 'PHI2PSI', 'PSI2PHI', 'XXXXX']
        for deleted_block in deleted_blocks:
            self.assertFalse(deleted_block in blocks,
                             f'{deleted_block} should have been deleted.')

    def test_pi(self):
        self.assertAlmostEqual(insel.block('pi'), math.pi, places=6)

    def test_constants(self):
        # Solar constant. Should it be 1361?
        # https://en.wikipedia.org/wiki/Solar_constant
        self.assertAlmostEqual(insel.block('gs'), 1367)
        self.assertAlmostEqual(insel.block('e'), math.exp(1), places=6)
        # Elementary charge
        self.assertAlmostEqual(insel.block('q'), 1.60217663e-19, delta=1e-23)
        # Boltzmann
        self.assertAlmostEqual(insel.block('k'), 1.380649e-23, delta=1e-27)
        # Reduced Planck
        self.assertAlmostEqual(insel.block(
            'hbar'), 1.05457182e-34, delta=1e-38)
        # Planck
        self.assertAlmostEqual(insel.block('h'), 6.626176e-34, delta=1e-38)
        # Stefan-Boltzmann
        self.assertAlmostEqual(insel.block(
            'sigma'), 5.670374419e-8, delta=1e-12)
        # Dilution factor... nowhere else to be seen
        #       The F block provides the \textit{dilution factor}: the ratio of irradiances
        #       between the solar constant on Earth, and the irradiance at the
        #       solar surface. $\frac{\mathrm{Sun\_Radius}^2}{\mathrm{Astronomical\_Unit}^2}$
        self.assertAlmostEqual(insel.block('f'), 696**2 / 149600**2)

    def test_and(self):
        self.assertAlmostEqual(insel.block('and', 1, 1), 1)
        self.assertAlmostEqual(insel.block('and', 0, 1), 0)
        self.assertAlmostEqual(insel.block('and', 1, 0), 0)
        self.assertAlmostEqual(insel.block('and', 0, 0), 0)
        self.assertAlmostEqual(insel.block('and', 2, 2), 0)
        self.compareLists(Insel.last_warnings,
                ['W05052 Block 00003: Invalid non logical input',
                 'W05053 Block 00003: Calls with invalid non logical input: 1'])
        self.assertAlmostEqual(insel.block('and', 0.9, 1.1), 1)

    def test_or(self):
        self.assertAlmostEqual(insel.block('or', 1, 1), 1)
        self.assertAlmostEqual(insel.block('or', 0, 1), 1)
        self.assertAlmostEqual(insel.block('or', 1, 0), 1)
        self.assertAlmostEqual(insel.block('or', 0, 0), 0)
        self.assertAlmostEqual(insel.block('or', 2, 2), 0)
        self.assertAlmostEqual(insel.block('or', 0.1, 1.1), 1)

    def test_xor(self):
        self.assertAlmostEqual(insel.block('xor', 1, 1), 0)
        self.assertAlmostEqual(insel.block('xor', 0, 1), 1)
        self.assertAlmostEqual(insel.block('xor', 1, 0), 1)
        self.assertAlmostEqual(insel.block('xor', 0, 0), 0)
        self.assertAlmostEqual(insel.block('xor', 2, 2), 0)
        self.assertAlmostEqual(insel.block('xor', 0.1, 1.1), 1)

    def test_inv(self):
        self.assertAlmostEqual(insel.block('inv', 1), 0)
        self.assertAlmostEqual(insel.block('inv', 0), 1)
        self.assertAlmostEqual(insel.block('inv', 2), 1)
        self.assertAlmostEqual(insel.block('inv', -1), 1)
        self.assertAlmostEqual(insel.block('inv', math.nan), 1)
        self.assertAlmostEqual(insel.block('inv', math.inf), 1)

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
        self.assertAlmostEqual(insel.block(
            'if', 3.14, float('inf')), 3.14, places=6)
        #  Weird, actually. It should be empty. Seems to require a DO block
        self.assertAlmostEqual(insel.block('if', 3.14, 0), 0.0, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, 0.4), 0.0, places=6)
        self.assertAlmostEqual(insel.block('if', 3.14, -0.4), 0.0, places=6)
        self.assertNaN(insel.block('if', float('nan'), 1))
        self.assertAlmostEqual(insel.block(
            'if', 3.14, float('nan')), 0.0, places=6)

    def test_ifelsenan(self):
        self.assertAlmostEqual(insel.block(
            'ifelsenan', 3.14, 1), 3.14, places=6)
        self.assertAlmostEqual(insel.block(
            'ifelsenan', 3.14, 2), 3.14, places=6)
        self.assertAlmostEqual(insel.block(
            'ifelsenan', 3.14, 0.5), 3.14, places=6)
        self.assertAlmostEqual(insel.block(
            'ifelsenan', 3.14, -0.5), 3.14, places=6)
        self.assertAlmostEqual(insel.block(
            'ifelsenan', 3.14, float('inf')), 3.14, places=6)
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
        self.assertRaisesRegex(InselError, "Too few", insel.block, 'diff')
        self.assertRaisesRegex(InselError, "Too few", insel.block, 'diff', 1)
        self.assertRaisesRegex(InselError, "Too many",
                               insel.block, 'diff', 1, 2, 3)

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
        self.assertRaisesRegex(InselError, "Zero .+ invalid",
                               insel.block, 'att', 1, parameters=[0])
        # Multiple inputs
        results = insel.block('att', 9, 3, 6, 7.5, parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[3.0, 1.0, 2.0, 2.5]')

    def test_div(self):
        self.assertAlmostEqual(insel.block('div',
                                           3, 2), 1.5, places=8)
        # Division by 0
        self.assertNaN(insel.block('div', 1, 0))
        self.compareLists(Insel.last_warnings,
                          ['W05001 Block 00003: Division by zero',
                           'W05002 Block 00003: Number of divisions by zero: 1'])

    def test_sine(self):
        self.assertAlmostEqual(insel.block('sin', 0), 0)
        self.assertAlmostEqual(insel.block('sin', 180), 0, places=6)
        self.assertAlmostEqual(insel.block('sin', 45), 2 ** 0.5 / 2, places=6)
        self.assertAlmostEqual(insel.block('sin', 30), 0.5, places=6)
        self.assertAlmostEqual(insel.block('sin', 60), 3 ** 0.5 / 2, places=6)
        self.assertAlmostEqual(insel.block('sin', 90), 1)
        self.assertAlmostEqual(insel.block('sin', -90), -1)
        self.assertAlmostEqual(insel.block(
            'sin', math.pi, parameters=[1]), 0, places=6)
        self.assertAlmostEqual(insel.block(
            'sin', math.pi / 2, parameters=[1]), 1, places=6)
        self.assertAlmostEqual(insel.block(
            'sin', math.pi / 6, parameters=[1]), 0.5, places=6)
        self.assertAlmostEqual(insel.block(
            'sin', -math.pi / 2, parameters=[1]), -1, places=6)

    def test_cosine(self):
        self.assertAlmostEqual(insel.block('cos', 0), 1)
        self.assertAlmostEqual(insel.block('cos', 180), -1, places=6)
        self.assertAlmostEqual(insel.block('cos', 45), 2 ** 0.5 / 2, places=6)
        self.assertAlmostEqual(insel.block('cos', 30), 3 ** 0.5 / 2, places=6)
        self.assertAlmostEqual(insel.block('cos', 60), 0.5, places=6)
        self.assertAlmostEqual(insel.block('cos', 90), 0)
        self.assertAlmostEqual(insel.block('cos', -90), 0)
        self.assertAlmostEqual(insel.block(
            'cos', math.pi, parameters=[1]), -1, places=6)
        self.assertAlmostEqual(insel.block(
            'cos', math.pi / 2, parameters=[1]), 0, places=6)
        self.assertAlmostEqual(insel.block(
            'cos', math.pi / 3, parameters=[1]), 0.5, places=6)
        self.assertAlmostEqual(insel.block(
            'cos', -math.pi / 2, parameters=[1]), 0, places=6)

    def test_atan2(self):
        self.assertAlmostEqual(insel.block('atan2', 1, 1), 45)
        self.assertAlmostEqual(insel.block('atan2', 0, 1), 0)
        self.assertAlmostEqual(insel.block('atan2', 1, 0), 90)
        self.assertAlmostEqual(insel.block('atan2', -1, -1), -135)
        self.assertAlmostEqual(insel.block(
            'atan2', 1, 1, parameters=[1]), math.pi / 4)
        self.assertAlmostEqual(insel.block(
            'atan2', 1, 0, parameters=[1]), math.pi / 2, places=6)
        self.assertNaN(insel.block('atan2', math.nan, 1))
        self.assertNaN(insel.block('atan2', 1, math.nan))

    def test_atan(self):
        self.assertAlmostEqual(insel.block('atan', 1), 45)
        self.assertAlmostEqual(insel.block('atan', 0), 0)
        self.assertAlmostEqual(insel.block('atan', math.inf), 90, places=4)
        self.assertNaN(insel.block('atan', math.nan))

    def test_offset(self):
        self.assertAlmostEqual(insel.block('offset',
                                           3, parameters=[-2]), 1.0, places=8)
        # Multiple inputs
        results = insel.block('offset', 9, 3, 6, -10.5,
                              parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[12.0, 6.0, 9.0, -7.5]')

    def test_root(self):
        self.assertAlmostEqual(insel.block('root', 2,
                                           parameters=[2]), 2 ** 0.5, places=6)
        self.assertEqual(repr(insel.block('root', 9, 16, 25, parameters=[2], outputs=3)),
                         '[3.0, 4.0, 5.0]')

    def test_sqrt(self):
        self.assertAlmostEqual(insel.block('sqrt', 2), 2 ** 0.5, places=6)
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
        for x in [-50, -20, 20, 50, 80]:
            self.assertAlmostEqual(insel.block(
                'exp', x) / math.exp(x), 1, places=6)
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
        december = insel.block('mtm2', 12, parameters=[
                               'Strasbourg'], outputs=9)
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
        insel.block('MTMLALO', 5, parameters=STUTTGART)
        warnings = Insel.last_warnings
        self.assertTrue(len(warnings) >= 1, "A warning should be shown")
        self.assertTrue(
            "Block 00002: '48.77° N, 9.18° W' seems to be in the ocean" in str(warnings))
        self.assertTrue("MTMLALO is deprecated" in str(warnings))

        # ~225W/m² in june in Stuttgart
        self.assertEqual(insel.block('MTMLALO2', 6, parameters=STUTTGART), 225)
        self.assertEqual(Insel.last_warnings, [], 'No problem with correct convention')

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

        # It should work at the equator too:
        self.assertNotNaN(insel.block('moonae2', 2021, 11,
                          19, 12, parameters=[0, 0, 0]))

    def test_sunae(self):
        for mode in range(3):  # type: insel.Parameter
            # Tested with Stellarium
            sun_stuttgart = insel.block('SUNAE2',
                                        2021, 11, 18, 12, 0,
                                        parameters=[mode] + STUTTGART,
                                        outputs=4)
            # NOTE: Precision is pretty bad (+-0.06°). Why?
            # NOTE: Compared to https://levelup.gitconnected.com/python-sun-position-for-solar-energy-and-research-7a4ead801777, Holland & Michalsky seem less inprecise than Spencer
            # TODO: Check with detailed example from NREL
            self.compareLists(sun_stuttgart,
                              [177 + 50 / 60, 21 + 52 / 60 + 14 / 3600, -19 - 17 / 60, (23 + 51 / 60) * 15], places=0)

    def test_sunae_in_the_tropics(self):
        # SUNAE used to be broken in the tropics, and got azimuth in the wrong quadrant
        sun_azimuth = insel.block('SUNAE2', 2021, 6, 21, 6, 0,
                                  parameters=[0, 20, 0, 0])
        self.assertAlmostEqual(sun_azimuth, 67 + 42 / 60, places=1)

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

    def test_now(self):
        year, month, day, hour, minute, second = insel.block('NOW', outputs=6)
        microsecond = int((second % 1)*1e6)
        insel_now = datetime(int(year), int(month), int(day),
                             int(hour), int(minute), int(second), microsecond)
        python_now = datetime.now()

        self.assertAlmostEqual(insel_now, python_now,
                               delta=timedelta(seconds=5))

    def test_julian_day_number(self):
        """
        Julian day number is used for many astronomical calculations.
        """
        self.assertAlmostEqual(1_721_424, insel.block('julian', 1, 1, 1))
        self.assertAlmostEqual(2_415_021, insel.block('julian', 1900, 1, 1))
        self.assertAlmostEqual(2_451_545, insel.block('julian', 2000, 1, 1))
        self.assertAlmostEqual(2_459_694, insel.block('julian', 2022, 4, 24))
        self.assertAlmostEqual(2_488_069, insel.block('julian', 2099, 12, 31))

    def test_gregorian_date(self):
        self.compareLists(insel.block(
            'gregor', 2_415_021, outputs=3), [1900, 1, 1])
        self.compareLists(insel.block(
            'gregor', 2_451_545, outputs=3), [2000, 1, 1])
        self.compareLists(insel.block(
            'gregor', 2_459_694, outputs=3), [2022, 4, 24])
        self.compareLists(insel.block(
            'gregor', 2_488_069, outputs=3), [2099, 12, 31])

    def test_weighted_average(self):
        self.assertAlmostEqual(65, insel.block(
            'avew', 50, 80, parameters=[1, 1]))
        self.assertAlmostEqual(62, insel.block(
            'avew', 80, 50, parameters=[4, 6]))
        self.assertAlmostEqual(10, insel.block(
            'avew', 0, 10, parameters=[0, 1]))
        self.assertAlmostEqual(10, insel.block(
            'avew', 10, 0, parameters=[1, 0]))
        self.assertRaisesRegex(InselError, "Invalid parameter",
                               insel.block, 'avew', 0, 1, parameters=[0, 0])

    def test_min(self):
        self.assertAlmostEqual(1, insel.block('min', 1))
        self.assertAlmostEqual(-1, insel.block('min', -1, 1))
        self.assertAlmostEqual(1, insel.block('min', 1, math.inf))
        self.assertAlmostEqual(0, insel.block('min', 0, 1, 1000, 0.1))
        self.assertInf(insel.block('min', -math.inf, 1))
        self.assertNaN(insel.block('min', math.nan, 1, -1))

    def test_max(self):
        self.assertAlmostEqual(1, insel.block('max', 1))
        self.assertAlmostEqual(1, insel.block('max', -1, 1))
        self.assertAlmostEqual(1, insel.block('max', 1, -math.inf))
        self.assertAlmostEqual(1000, insel.block('max', 0, 1, 1000, 0.1))
        self.assertInf(insel.block('max', math.inf, 1))
        self.assertNaN(insel.block('max', math.nan, 1, -1))


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

    def test_mtm_averages(self):
        # Those places used to have wrong averages
        places = ['Cambridge', 'Inuvik', 'Milagro',
                  'Naesgard', 'Nurnberg', 'Planes de Montecrist']
        for place in places:
            self.assertTrue(insel.template('weather/check_temperatures', location=place),
                            f'Wrong temperatures for {place}')

    def test_gengt_consistency(self):
        deviation = insel.template('weather/gengt_comparison')
        # NOTE: Depending on system, pseudo random values can vary very slightly. 1e-4 really isn't any problem for °C or W/m²
        self.compareLists(deviation, [0, 0], places=4)

    def test_gengt_averages(self):
        irradiance_deviation, temperature_deviation = \
            insel.template('weather/gengt_monthly_averages')
        self.assertAlmostEqual(irradiance_deviation, 0, delta=5,
                               msg="Irradiance shouldnt vary by more than 5 W/m²")
        self.assertAlmostEqual(temperature_deviation, 0, delta=0.1,
                               msg="Temperature shouldnt vary by more than 0.1K")

    def test_aligned_screen_block(self):
        # Check that numbers displayed by SCREEN '*' are separated by at least one space
        # and that the decimal separators are aligned one above the other
        matrix = insel.template('expg')
        for i, row in zip(range(-20, 20), matrix):
            power = i / 2
            self.assertAlmostEqual(power, row[0], places=6)
            r1 = 10 ** power
            r2 = -10 ** (-power)
            self.assertAlmostEqual(r1, row[1], delta=r1 / 1e6)
            self.assertAlmostEqual(r2, row[2], delta=-r2 / 1e6)

        # Run again, this time checking the nicely formatted raw output.
        aligned = insel.raw_run('templates/expg.insel')
        output = [line for line in aligned.splitlines() if '    ' in line]
        self.assertTrue(len(output) > 30, 'Many lines should be returned.')

        dot_indices = set()
        columns = 5

        def indices(text, char):
            return [i for i, ltr in enumerate(text) if ltr == char]

        for line in output:
            dot_indices.update(indices(line, '.'))

        self.assertEqual(len(dot_indices), columns,
                         f"There should be {columns} nicely aligned decimal points")

    def test_updated_coordinates(self):
        v1_results = insel.template('photovoltaic/nurnberg_v1',
                                    latitude=49.5,
                                    old_longitude=-11.08,
                                    old_timezone=23
                                    )
        v2_results = insel.template('photovoltaic/nurnberg_v2',
                                    latitude=49.5,
                                    longitude=11.08,
                                    timezone=+1
                                    )
        self.compareLists(v1_results, [3865, 3645], places=-1)
        self.compareLists(v2_results, v1_results, places=2)

    def test_cumc(self):
        table = insel.template('conditional/sum')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual(days * (days + 1) / 2 * 24, y)

    def test_maxxc(self):
        table = insel.template('conditional/max')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual(days, y)

    def test_max_xy(self):
        table = insel.template('stats/max_xy')
        self.compareLists(table, [90, 1])
        self.assertEqual(insel.template('stats/max_xy_c'),
                         [[2020, 31], [2021, 31]])
        table = [v for r in insel.template('stats/max_xy_p') for v in r]
        self.compareLists(table, [90, 1, 360, 0], places=6)

    def test_min_xy(self):
        table = insel.template('stats/min_xy')
        self.compareLists(table, [270, -1])
        self.assertEqual(insel.template('stats/min_xy_c'),
                         [[2020, 29], [2021, 28]])
        table = [v for r in insel.template('stats/min_xy_p') for v in r]
        self.compareLists(table, [0, 0, 270, -1], places=6)

    def test_minnc(self):
        table = insel.template('conditional/min')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual(-days, y)

    def test_avec(self):
        table = insel.template('conditional/average')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual((days + 1) / 2, y)

    def test_parametric_average(self):
        self.assertEqual(1, insel.template('parametric/average'))

    def test_parametric_max(self):
        self.assertEqual(1, insel.template('parametric/max'))

    def test_parametric_min(self):
        self.assertEqual(1, insel.template('parametric/min'))

    def test_a_times_b(self):
        self.assertAlmostEqual(insel.template('a_times_b'), 9, places=6)
        # NOTE: .insel can be included in template_name, but doesn't have to.
        self.assertAlmostEqual(insel.template(
            'a_times_b.insel', a=4), 12, places=6)
        # NOTE: template path can also be absolute.
        self.assertAlmostEqual(insel.template(SCRIPT_DIR / 'templates' / 'a_times_b.insel', a=4, b=5),
                               20, places=6)

    def test_non_ascii_template(self):
        utf8_template = insel.Template('a_times_b_utf8', a=2, b=2)
        utf8_template.timeout = 5
        self.assertEqual(utf8_template.run(), 4)

        iso_template = insel.Template('a_times_b_iso8859', a=4, b=4)
        iso_template.timeout = 5
        self.assertEqual(iso_template.run(), 16)

    def test_sunpower_isc(self):
        self.assertRaisesRegex(AttributeError, "UndefinedValue", insel.template,
                               'photovoltaic/i_sc')  # Missing pv_id. STC by default
        spr_isc = insel.template('photovoltaic/i_sc', pv_id='008823')
        self.assertIsInstance(spr_isc, float)
        self.assertAlmostEqual(spr_isc, 5.87, places=2)

        self.assertAlmostEqual(insel.template('photovoltaic/i_sc', pv_id='003305'),
                               5.96, places=2)
        # TODO: More research is needed :)
        self.skipTest("""This spec fails, probably because of a too low
                'Temperature coeff of short-circuit current' in .bp files
                 .982E-7 in this example, instead of ~0.2E-3""")
        self.assertAlmostEqual(insel.template('photovoltaic/i_sc', pv_id='003305', temperature=70),
                               5.96 + (70 - 25) * 3.5e-3, places=2)

    def test_sunpower_uoc(self):
        # Missing pv_id. STC by default
        self.assertRaises(AttributeError, insel.template, 'photovoltaic/u_oc')
        self.assertAlmostEqual(insel.template('photovoltaic/u_oc', pv_id='003305'),
                               64.2, places=2)
        temp = 70
        # TODO: More research is needed :)
        self.skipTest("Not sure about this calculation.")
        self.assertAlmostEqual(insel.template('photovoltaic/u_oc', pv_id='003305', temperature=temp),
                               64.2 + (temp - 25) * (-0.1766), places=2)

    def test_sunpower_mpp(self):
        # Missing pv_id. STC by default
        self.assertRaises(AttributeError, insel.template, 'photovoltaic/mpp')
        self.assertAlmostEqual(insel.template('photovoltaic/mpp', pv_id='003305'),
                               305, places=0)
        temp = 70
        # TODO: Check with PVSYST or PVLIB. Is this the correct formula?
        # NOTE: -0.38%/K P_mpp, according to SPR 305 manual (https://www.pocosolar.com/wp-content/themes/twentyfifteen/pdfs/Sunpower%20Solar%20Panels/sunpower_305wht_spec_sheet.pdf)
        self.assertAlmostEqual(insel.template('photovoltaic/mpp', pv_id='003305', temperature=temp),
                               305 * (1 - 0.38 / 100) ** (temp - 25), places=0)

    def test_write_block(self):
        self.run_write_block()
        self.run_write_block(overwrite=0)
        self.run_write_block(overwrite=1)
        self.run_write_block(overwrite=2)

        self.run_write_block(basename='Ñüößç&txt.täxt€',
                             header='#ßeäöütµ§%&²³@°')

        self.run_write_block(basename='with a space.txt')
        self.run_write_block(basename='with_underscore.txt')

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
            model = insel.Template(
                'io/write_params', dat_file=dat_file, **write_params)
            model.run()
            self.assertEqual(model.warnings, [])
            self.assertTrue(dat_file.exists(), "File should have been written")
            with open(dat_file) as out:
                if write_params.get('header'):
                    next(out)
                content = out.readlines()
                written = [float(line.split(separator)[0]) for line in content]
                self.compareLists(written, range(1, 11), places=5)

    def test_read_simple_file(self):
        fourfivesix = insel.template('io/read_simple_file', ext='dat')
        self.compareLists(fourfivesix, [4, 5, 6])

    def test_read_missing_file(self):
        self.assertRaisesRegex(InselError, "(?m)^F05029 Block 00001: Cannot open file: .*not_here$",
                               insel.template, 'io/not_here')

    def test_read_too_many_lines(self):
        fourfivesix = insel.template('io/read_simple_file', ext='dat', lines=5)
        self.compareLists(fourfivesix, [4, 5, 6])
        self.compareLists(Insel.last_warnings, ['F05031 Block 00002: Unexpected end of file - simulation terminated'])

    def test_read_csv_like_as_normal_file(self):
        # READ block used to completely skip CSV files :-/
        # Now it just tries to read it as a normal file
        fourfivesix = insel.template('io/read_simple_file', ext='csv')
        self.compareLists(fourfivesix, [4, 5, 6])

    def test_read_epw_file(self):
        # Depending on extension, READ block will parse as normal file or EPW
        stuttgart_epw_average_temp = insel.template(
            'io/read_epw_file', ext='epw')
        self.assertAlmostEqual(stuttgart_epw_average_temp, 9.1, places=1)
        nothing_to_read = insel.template('io/read_epw_file', ext='txt')
        self.assertEqual(nothing_to_read, [])

    def test_weird_output(self):
        floats_and_lists = insel.template('io/weird_output')
        out = ';'.join(sorted(str(x) for x in floats_and_lists))
        self.assertEqual(
            out, '1.0;2.0;[1.0, 1.0, 1.0];[1.0, 1.0];[2.0, 2.0, 2.0];[2.0, 2.0]')


class TestExistingModel(CustomAssertions):
    def test_one_to_ten(self):
        self.compareLists(
            insel.run('templates/one_to_ten.insel'), range(1, 11))

    def test_nonexisting_model(self):
        self.assertRaisesRegex(InselError, "File not found",
                               insel.run, 'templates/not_here.insel')
        self.assertRaisesRegex(InselError, "File not found",
                               insel.run, 'not_here/model.insel')

    def test_not_an_insel_file(self):
        self.assertRaisesRegex(InselError, "Invalid INSEL model file extension",
                               insel.run, 'data/gengt_comparison.dat')
        self.assertRaisesRegex(InselError, "Invalid INSEL model file extension",
                               insel.run, 'not_even_a_file.csv')

    def test_insel_constants(self):
        self.assertEqual(insel.run('templates/insel_constants.insel'), 3)

    def test_insel_include(self):
        self.assertEqual(insel.run('templates/insel_include.insel'), 3)

    def test_merging_two_loops(self):
        self.assertRaisesRegex(InselError, "Please try to merge 2 & 3", insel.run,
                               'templates/merge_distinct_loops.insel')

    def test_read_relative_file_when_in_correct_folder(self):
        with cwd(SCRIPT_DIR / 'templates'):
            deviation = insel.run('io/read_relative_file.insel')
            self.compareLists(deviation, [0, 0], places=4)

    def test_read_relative_file_when_in_another_folder(self):
        with cwd(SCRIPT_DIR):
            deviation = insel.run('templates/io/read_relative_file.insel')
            self.compareLists(deviation, [0, 0], places=4)

    def test_can_read_relative_file_with_absolute_path(self):
        with cwd(Path.home()):
            deviation = insel.run(
                SCRIPT_DIR / 'templates' / 'io' / 'read_relative_file.insel')
            self.compareLists(deviation, [0, 0], places=4)

    def test_string_parameter_in_vseit_should_not_be_cut(self):
        for f in ['short_string.vseit', 'long_string.vseit']:
            insel_model = insel.raw_run('-m', 'templates/io/' + f)
            string_params = [
                p for p in insel_model.split() if p.count("'") == 2]
            self.assertEqual(len(string_params), 2,
                             f"2 string parameters should be found in {f}")

    def test_screen_headline_should_be_displayed(self):
        for f in ['short_string.vseit', 'long_string.vseit']:
            out = insel.raw_run('templates/io/' + f)
            lines = out.splitlines()
            headline = next(line for line in lines if 'String' in line)
            self.assertTrue(len(headline) < 100,
                            f"Headline '{headline}' shouldn't be too long")

    def test_screen_utf8_header_should_be_displayed(self):
        out = insel.raw_run('templates/io/utf_headline.insel')
        self.assertTrue('T€st 12345' in out,
                        "Headline should be allowed to be in UTF-8")


class TestInselFlags(unittest.TestCase):
    def test_insel(self):
        just_insel = insel.raw_run()
        for part in [r'This is INSEL \d\.\d\.\d', '(32|64) bit',
                     '-d', '-l', '-m', '-v', '-b']:
            self.assertRegex(just_insel, part,
                             f"'{part}' should be printed out by 'insel'")

    def test_insel_v(self):
        insel_v = insel.raw_run('-v')
        for part in ['libInselEngine', 'libInselBridge', 'libInselTools',
                     'libInselFB', 'libInselEM', 'libInselSE', r'_20\d\d\d\d\d\d_',
                     # gcc __DATE__ __TIME__ format. e.g. "Mar 31 2022 13:42:25"
                     r'[A-Z][a-z][a-z] [ \d]\d 20\d\d \d\d:\d\d:\d\d']:
            self.assertRegex(insel_v, part,
                             f"'{part}' should be printed out by 'insel -v'")

    def test_insel_l(self):
        insel_l = insel.raw_run('-l', 'templates/one_to_ten.insel')
        for part in ['1\s*DO\s*T', '2\s*SCREEN\s*S']:
            self.assertRegex(insel_l, part,
                             f"'{part}' should be printed out by 'insel -l'")

    def test_insel_s(self):
        insel_s = insel.raw_run('-s', 'templates/io/short_string.vseit')
        self.assertRegex(insel_s, '0 errors, 0 warnings',
                         "insel -s should check model")

    def test_insel_m(self):
        insel_m = insel.raw_run('-m', 'templates/io/short_string.vseit')
        for part in ['b\s+1\s+DO', 'b\s+2\s+SCREEN', "'*'", "'ShortString'"]:
            self.assertRegex(insel_m, part,
                             f"'{part}' should be printed out by 'insel -l'")

    def test_insel_d(self):
        insel_d = insel.raw_run('-d', 'templates/one_to_ten.insel')
        for part in ['Compiling', 'Constructor call', 'Destructor call', 'Standard call',
                     'block DO', 'block SCREEN']:
            self.assertRegex(insel_d, part,
                             f"'{part}' should be printed out by 'insel -d'")


class TestUserBlocks(CustomAssertions):
    def test_ubstorage(self):
        insel.block('ubstorage', 1, 2, parameters=[
                    10, 0, 1, 1, 0, 100, 0, 1, 0])

    def test_ubisonland(self):
        self.assertAlmostEqual(insel.block('ubisonland', 48.77, 9.18), 1)
        self.assertAlmostEqual(insel.block('ubisonland', 48.77, -9.18), 0)

    # TODO: Test UBCHP


if __name__ == '__main__':
    with cwd(SCRIPT_DIR):
        unittest.main(exit=False)
        print(f'Total INSEL calls : {Insel.calls}')
