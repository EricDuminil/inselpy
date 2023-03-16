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


if __name__ == '__main__':
    unittest.main(exit=False)
