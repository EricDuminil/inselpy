# coding=utf8
import unittest
import math
import logging
from pathlib import Path
import contextlib
from typing import List
import platform
import insel
from insel import Insel, InselError
from .custom_assertions import CustomAssertions

logging.basicConfig(level=logging.ERROR)

SCRIPT_DIR = Path(__file__).resolve().parent
IS_WINDOWS = platform.system().lower() == 'windows'

# TODO: Test with LC_ALL = DE ?
# TODO: Test PVDET1
# TODO: Test if insel_gui is installed?
# TODO: Add gnuplot tests
# TODO: Test inselHelp installed?
# FIXME: Algebraic loops seem to break INSEL. Test & fix


@contextlib.contextmanager
def cwd(path):
    import os
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


cwd(SCRIPT_DIR)


# INSEL 8.3 convention
STUTTGART = [48.77, 9.18, 1]  # type: List[insel.Parameter]
IMPORTANT_BLOCKS = ['MUL', 'PI', 'PVI', 'MPP', 'DO', 'CLOCK']


class TestExistingModel(CustomAssertions):
    def test_one_to_ten(self):
        self.compareLists(
            insel.run('templates/one_to_ten.insel'), range(1, 11))

    def test_screen(self):
        self.compareLists(insel.run('templates/io/screen.insel'), [1, 2, 3])
        header_content = insel.raw_run('templates/io/screen_header.insel')
        self.assertTrue('# HASHTAG' in header_content)
        self.assertTrue('! EXCLAMATION' in header_content)

    def test_screen1g(self):
        self.compareLists(insel.run('templates/io/screen1g.insel'), [])

    def test_add_negative_inputs(self):
        # Little known feature. Could be deleted.
        self.assertEqual(insel.template('add_negative_inputs.insel'), -8)

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

    def test_insel_duplicate_constant(self):
        self.assertEqual(
            insel.run('templates/duplicate_constant.insel'), 12345)
        self.assertEqual(Insel.last_warnings,
                         ['W04024 Redefinition of constant TEST skipped'])

    def test_insel_empty_constant(self):
        self.assertEqual(insel.run('templates/empty_constant.insel'), 12345)
        self.assertRegex(Insel.last_raw_output,
                         ("W05313 Stray constant definition detected at line 00003"
                          " of file .*empty_constant.insel"))

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

    def test_mpp_without_top_of_loop(self):
        self.assertRaisesRegex(InselError, "No TOL-block", insel.run,
                               'templates/photovoltaic/mpp_without_top_of_loop.vseit')

    def test_mpp_with_top_of_loop(self):
        out = insel.raw_run('templates/photovoltaic/mpp_with_top_of_loop.vseit')
        self.assertRegex(out, r'Maximum at 17\.3 Volt and 52\.6 Watt')

    def test_algebraic_loop(self):
        self.assertRaisesRegex(InselError, "Algebraic loop detected", insel.run,
                               'templates/engine/sum_sum_do.insel')

    def test_algebraic_loop_with_do_do(self):
        self.skipTest("templates/engine/do_do.insel fails with SIGSEGV")

    def test_algebraic_loop_with_sum_sum(self):
        self.skipTest("templates/engine/sum_sum.insel fails with SIGSEGV")


class TestInselFlags(unittest.TestCase):
    def test_insel(self):
        just_insel = insel.raw_run()
        for part in [r'This is INSEL \d\.\d\.\d', '(32|64) bit for (Linux|Windows|macOS)',
                     '-d', '-l', '-m', '-v', '-b']:
            self.assertRegex(just_insel, part,
                             f"'{part}' should be printed out by 'insel'")

    def test_insel_v(self):
        insel_v = insel.raw_run('-v')
        for part in ['libInselEngine', 'libInselBridge', 'libInselTools',
                     'libInselFB', 'libInselEM', 'libInselSE', r'_20\d\d\-\d\d\-\d\d_',
                     # gcc __DATE__ __TIME__ format. e.g. "Mar 31 2022 13:42:25"
                     r'[A-Z][a-z][a-z] [ \d]\d 20\d\d \d\d:\d\d:\d\d']:
            self.assertRegex(insel_v, part,
                             f"'{part}' should be printed out by 'insel -v'")

    def test_insel_l(self):
        insel_l = insel.raw_run('-l', 'templates/one_to_ten.insel')
        for part in [r'1\s*DO\s*T', r'2\s*SCREEN\s*S']:
            self.assertRegex(insel_l, part,
                             f"'{part}' should be printed out by 'insel -l'")

    def test_insel_s(self):
        insel_s = insel.raw_run('-s', 'templates/io/short_string.vseit')
        self.assertRegex(insel_s, '0 errors, 0 warnings',
                         "insel -s should check model")

    def test_insel_m(self):
        insel_m = insel.raw_run('-m', 'templates/io/short_string.vseit')
        for part in [r'b\s+1\s+DO', r'b\s+2\s+SCREEN', "'*'", "'ShortString'"]:
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

    def test_modulo(self):
        self.assertAlmostEqual(self.expr('x % y', 111, 7), 6)

    def test_nan(self):
        self.assertNaN(self.expr('0/0'))

    def test_logic(self):
        self.assertEqual(self.expr('or(3 < 1, 2 > 3)'), 0)
        self.assertEqual(self.expr('or(3 < 1, 2 < 3)'), 1)
        self.assertEqual(self.expr('and(3 < 1, 2 < 3)'), 0)
        self.assertEqual(self.expr('and(3 >= 1, 2 < 3)'), 1)
        self.assertEqual(self.expr('0 || 0'), 0)
        self.assertEqual(self.expr('1 || 0 || 0'), 1)
        self.assertEqual(self.expr('1 && 0'), 0)
        self.assertEqual(self.expr('1 && 1'), 1)

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


class TestInselDoc(unittest.TestCase):
    def test_insel_pdfs(self):
        doc_dir = Insel.dirname / 'doc'
        for basename in ['Tutorial', 'BlockReference', 'UserBlockReference',
                         'GettingStarted', 'ProgrammersGuide']:
            pdf = doc_dir / f"insel{basename}_en.pdf"
            self.assertTrue(pdf.exists(), f"{pdf} should exist")
            self.assertTrue(pdf.stat().st_size > 100_000,
                            f"{pdf} should be large enough")

    def test_insel_block_pdfs(self):
        doc_dir = Insel.dirname / 'doc' / 'inselBlocks'
        for basename in IMPORTANT_BLOCKS:
            pdf = doc_dir / f"{basename}.pdf"
            self.assertTrue(pdf.exists(), f"{pdf} should exist")
            self.assertTrue(pdf.stat().st_size > 10_000,
                            f"{pdf} should be large enough")


if __name__ == '__main__':
    unittest.main(exit=False)
    print(f'Total INSEL calls : {Insel.calls}')
