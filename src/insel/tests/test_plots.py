import os
from pathlib import Path

import insel

from .constants import SCRIPT_DIR
from .custom_assertions import CustomAssertions

os.chdir(SCRIPT_DIR)


class TestBasicPlots(CustomAssertions):
    def test_plot_sin(self):
        png_output = Path("plots/sine.png")
        png_output.unlink(missing_ok=True)
        insel.plot("plots/sine", x_max=720)
        self.assertTrue(
            png_output.exists(),
            rf"{png_output} should have been written.\ņPlease update INSEL to 8.4 if this test fails",
        )
