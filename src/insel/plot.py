from typing import Union
import subprocess
from .template import Template
from .model import Row, Table

GNUPLOT_COMMAND = 'gnuplot'


class Plot(Template):
    """Insel Template + Gnuplot Template"""

    def run(self) -> Union[float, Row, Table]:
        result = super().run()
        self._plot()
        return result

    def _plot(self):
        gnuplot_path = self.template_full_path().with_suffix('.gnuplot')

        return subprocess.check_output(
            [GNUPLOT_COMMAND, gnuplot_path.absolute().as_posix()], shell=False)
