# coding=utf8
import insel
from .custom_assertions import CustomAssertions


class TestUserBlocks(CustomAssertions):
    def test_ubstorage(self):
        insel.block('ubstorage', 1, 2, parameters=[
                    10, 0, 1, 1, 0, 100, 0, 1, 0])

    def test_ubisonland(self):
        self.assertAlmostEqual(insel.block('ubisonland', 48.77, 9.18), 1)
        self.assertAlmostEqual(insel.block('ubisonland', 48.77, -9.18), 0)

    # TODO: Test UBCHP
