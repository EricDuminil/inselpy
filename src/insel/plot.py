import os
import re
import tempfile
from pathlib import Path
from typing import Union
import subprocess
from .template import Template
from .model import Row, Table
from .insel import Insel

COMMAND = 'gnuplot'
EXT = '.gnuplot'


class Plot(Template):
    """Insel Template + Gnuplot Template"""
    # TODO: Document
    # TODO: Should work with standard gnuplot files too, straight from VSEIT

    def __init__(self, template_path, **parameters) -> None:
        super().__init__(template_path, **parameters)
        self.gnuplot_path = self.template_full_path().with_suffix(EXT)

    def run(self) -> Union[float, Row, Table]:
        result = super().run()
        self._plot()
        return result

    def add_defaults_to(self, parameters):
        parameters = super().add_defaults_to(parameters)
        defaults = {
            'plot_folder': Path('plots/'),
            'result_folder': Insel.plot_path.as_posix()
        }
        defaults.update(parameters)
        return defaults

    def _plot_content(self):
        with open(self.gnuplot_path,
                  encoding='utf-8',
                  errors='backslashreplace') as template:
            content = template.read()
            content = re.sub(Template.placeholder_pattern,
                             self.replace_placeholders, content)
            return content

    def _temp_gnuplot(self):
        return tempfile.NamedTemporaryFile(mode='w+', suffix=EXT,
                                           prefix=f'{self.name}_', delete=False)

    def _plot(self):
        try:
            with self._temp_gnuplot() as temp_plot:
                temp_path = temp_plot.name
                temp_plot.write(self._plot_content())
            return subprocess.check_output([COMMAND, temp_path],
                                           shell=False)
        finally:
            os.remove(temp_path)
