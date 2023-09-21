# coding=utf8
import math
from collections import Counter
from datetime import datetime, timedelta
import insel
from insel import Insel, InselError
from .custom_assertions import CustomAssertions
from .constants import STUTTGART, IMPORTANT_BLOCKS


class TestBlock(CustomAssertions):
    def test_blocks_are_unique(self):
        insel_b = insel.raw_run('-b')
        blocks = Counter(b.strip()
                         for b in insel_b.rsplit('\n\n', maxsplit=1)[-1].split('\n'))
        self.assertTrue(len(blocks) > 390, "There should be many blocks")
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
        blocks = set(b.strip() for b in insel_b.rsplit('\n\n', maxsplit=1)[-1].split('\n'))
        deleted_blocks = ['DRY', 'FURWALL', 'FURWALL2', 'GASIF',
                          'GENBOD', 'GOMPERTZ', 'HEATEX', 'MIXING', 'OPTIM',
                          'PRIMARY', 'SECON1', 'SECON2', 'TIMEMS', 'TIMEMS0',
                          'DIV2', 'NOW0', 'EPLUS', 'PHI2PSI', 'PSI2PHI', 'XXXXX', 'SCREENG']
        for important_block in IMPORTANT_BLOCKS:
            self.assertTrue(important_block in blocks,
                            f'{important_block} should be displayed by insel -b')
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
        self.assertEqual(Insel.last_warnings,
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
        self.assertRegex(Insel.last_raw_output, '1 errors?, 0 warnings?')
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

        self.assertRegex(Insel.last_raw_output, '1 errors?, 0 warnings?')
        # Multiple inputs
        results = insel.block('att', 9, 3, 6, 7.5, parameters=[3], outputs=4)
        self.assertEqual(repr(results), '[3.0, 1.0, 2.0, 2.5]')

    def test_div(self):
        self.assertAlmostEqual(insel.block('div',
                                           3, 2), 1.5, places=8)
        # Division by 0
        self.assertNaN(insel.block('div', 1, 0))
        self.assertEqual(Insel.last_warnings,
                         ['W05001 Block 00003: Division by zero',
                          'W05002 Block 00003: Number of divisions by zero: 1'])

    def test_modulo(self):
        """
        https://gcc.gnu.org/onlinedocs/gfortran/MOD.html
        The returned value of A % P has the same sign as A and a magnitude less than the magnitude of P. 
        """

        self.assertAlmostEqual(insel.block('mod', 3, 2), 1)
        self.assertAlmostEqual(insel.block('mod', 4, 2), 0)
        self.assertAlmostEqual(insel.block('mod', 5, -2), 1)
        self.assertAlmostEqual(insel.block('mod', -11, 7), -4)
        self.assertAlmostEqual(insel.block('mod', -11, -7), -4)
        self.assertAlmostEqual(insel.block('mod', 3.5, 1), 0.5)
        self.assertAlmostEqual(insel.block('mod', 1.2, 0.5), 0.2)
        # Division by 0
        self.assertNaN(insel.block('mod', 1, 0))
        self.assertEqual(Insel.last_warnings,
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
        for exponent in [-50, -20, 20, 50, 80]:
            self.assertAlmostEqual(insel.block('exp', exponent) / math.exp(exponent), 1, places=6)
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

    def test_mtm_with_unknown_location(self):
        self.assertRaisesRegex(InselError, "Location not found",
                               insel.block, 'mtm2', 1, parameters=["NOT_A_CITY"])

    def test_mtm_with_incorrect_input(self):
        insel.block('MTM2', 13, parameters=['Tokyo'])
        warnings = Insel.last_warnings
        self.assertTrue(len(warnings) >= 1, "A warning should be shown")
        self.assertTrue(
            "Block 00002: Invalid input" in str(warnings))

    def test_mtmlalo(self):
        insel.block('MTMLALO', 5, parameters=STUTTGART)
        warnings = Insel.last_warnings
        self.assertRegex(Insel.last_raw_output, '0 errors?, 1 warnings?')
        self.assertTrue(len(warnings) >= 1, "A warning should be shown")
        self.assertTrue(
            "Block 00002: '48.77° N, 9.18° W' seems to be in the ocean" in str(warnings))
        self.assertTrue("MTMLALO is deprecated" in str(warnings))

        # ~225W/m² in june in Stuttgart
        self.assertEqual(insel.block('MTMLALO2', 6, parameters=STUTTGART), 225)
        self.assertEqual(Insel.last_warnings, [],
                         'No problem with correct convention')

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
            # NOTE: Compared to
            #       https://levelup.gitconnected.com/python-sun-position-for-solar-energy-and-research-7a4ead801777,
            #       Holland & Michalsky seem less inprecise than Spencer
            # TODO: Check with detailed example from NREL
            self.compareLists(sun_stuttgart,
                              [177 + 50 / 60, 21 + 52 / 60 + 14 / 3600,
                               -19 - 17 / 60, (23 + 51 / 60) * 15],
                              places=0)

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

    def test_screen(self):
        # SCREEN has no output
        self.assertRaisesRegex(InselError, "Invalid output",
                               insel.block, 'screen')

    def test_screen1g(self):
        # SCREEN1G has no output
        self.assertRaisesRegex(InselError, "Invalid output",
                               insel.block, 'screen1g')


class TestGenericExpression(CustomAssertions):
    def expr(self, expression, *args):
        return insel.block('expression', *args, parameters=[expression])

    def test_constant(self):
        self.assertAlmostEqual(self.expr('(1 + sqrt(5)) / 2'), (1+5**0.5)/2)
        # https://xkcd.com/1047/:
        self.assertAlmostEqual(self.expr('sqrt(3) / 2  - e / pi'), 0, delta=1e-3)

    def test_power(self):
        self.assertEqual(self.expr('2^4'), 16)
        self.assertEqual(self.expr('3^3'), 27)
        self.assertEqual(self.expr('-1^2'), -1)

    def test_one_input(self):
        self.assertAlmostEqual(self.expr('cos(x)', math.pi), -1)

    def test_two_inputs(self):
        self.assertAlmostEqual(self.expr('x*y', 2, 3), 6)
        self.assertAlmostEqual(self.expr('x*x > y*y', -4, 2), 1)
        self.assertAlmostEqual(self.expr('AVERAGE(x, y)', 3, 12), 7.5)

    def test_three_inputs(self):
        self.assertAlmostEqual(self.expr('(x*y*z)*x^2', -1, 2, 3.5), -7)

    def test_modulo_expr(self):
        self.assertAlmostEqual(self.expr('x % y', 111, 7), 6)

    def test_nan(self):
        self.assertNaN(self.expr('nan'))
        self.assertNaN(self.expr('nan + 2'))

    def test_logic(self):
        self.assertEqual(self.expr('or(3 < 1, 2 > 3)'), 0)
        self.assertEqual(self.expr('or(3 < 1, 2 < 3)'), 1)
        self.assertEqual(self.expr('and(3 < 1, 2 < 3)'), 0)
        self.assertEqual(self.expr('and(3 >= 1, 2 < 3)'), 1)
        self.assertEqual(self.expr('0 | 0'), 0)
        self.assertEqual(self.expr('1 | 0 | 0'), 1)
        self.assertEqual(self.expr('1 & 0'), 0)
        self.assertEqual(self.expr('1 & 1'), 1)

    def test_wrong_formulas(self):
        self.assertRaisesRegex(InselError, r" \^ First error is here",
                               self.expr, ') 2 + 3')
        self.assertRaisesRegex(InselError, r" __\^ First error is here",
                               self.expr, 'x + ')
        self.assertRaisesRegex(InselError, r" ________\^ First error is here",
                               self.expr, 'sin(1 * )')
        self.assertRaisesRegex(InselError, r" ____\^ First error is here",
                               self.expr, '1 + a + b')

    def test_missing_x(self):
        self.assertRaisesRegex(InselError, "Unknown variable 'x'",
                               self.expr, 'x + 3')

    def test_missing_y(self):
        self.assertRaisesRegex(InselError, "Unknown variable 'y'",
                               self.expr, 'x + y', 1)

    def test_missing_z(self):
        self.assertRaisesRegex(InselError, "Unknown variable 'z'",
                               self.expr, 'x + y + z', 1, 2)
