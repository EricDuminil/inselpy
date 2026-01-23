import os
from pathlib import Path
import insel
from .custom_assertions import CustomAssertions
from .constants import SCRIPT_DIR

os.chdir(SCRIPT_DIR)


class TestBasicPlots(CustomAssertions):
    def test_plot_sin(self):
        png_output = Path('plots/sine.png')
        png_output.unlink(missing_ok=True)
        insel.plot('plots/sine', x_max=720)
        self.assertTrue(png_output.exists(), f"{png_output} should have been written")
