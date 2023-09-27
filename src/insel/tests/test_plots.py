import os
import insel
from .custom_assertions import CustomAssertions
from .constants import SCRIPT_DIR

os.chdir(SCRIPT_DIR)


class TestBasicPlots(CustomAssertions):
    def test_plot_sin(self):
        print(insel.plot('plots/sine'))
