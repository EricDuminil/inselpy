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

    def test_double_plot(self):
        data_file_1 = insel.Insel.plot_path / 'insel.gpl'
        data_file_2 = insel.Insel.plot_path / 'insel2.gpl'
        data_file_1.unlink(missing_ok=True)
        data_file_2.unlink(missing_ok=True)
        txt_output = Path('plots/sorted_sine_and_cosine.txt')
        txt_output.unlink(missing_ok=True)
        insel.plot('plots/double_plot')
        self.assertTrue(txt_output.exists(), f"{txt_output} should have been written")
        self.assertTrue(data_file_1.exists(), f"{data_file_1} should have been written")
        self.assertTrue(data_file_2.exists(), f"{data_file_2} should have been written")
