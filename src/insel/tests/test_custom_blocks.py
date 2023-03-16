# coding=utf8
import unittest
import logging
import insel
from .custom_assertions import CustomAssertions

logging.basicConfig(level=logging.ERROR)


# TODO: Test with LC_ALL = DE ?
# TODO: Test PVDET1
# TODO: Test if insel_gui is installed?
# TODO: Add gnuplot tests
# TODO: Test inselHelp installed?
# FIXME: Algebraic loops seem to break INSEL. Test & fix


class TestUserBlocks(CustomAssertions):
    def test_ubstorage(self):
        insel.block('ubstorage', 1, 2, parameters=[
                    10, 0, 1, 1, 0, 100, 0, 1, 0])

    def test_ubisonland(self):
        self.assertAlmostEqual(insel.block('ubisonland', 48.77, 9.18), 1)
        self.assertAlmostEqual(insel.block('ubisonland', 48.77, -9.18), 0)

    # TODO: Test UBCHP


if __name__ == '__main__':
    unittest.main(exit=False)
