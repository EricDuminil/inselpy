import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Union

from .insel import Insel
from .model import Row, Table
from .template import Template

COMMAND = "gnuplot"
EXT = ".gnuplot"


class Plot(Template):
    """Runs an INSEL template and then renders the paired gnuplot script.

    Expects two files with the same basename inside the templates/ folder:
    * <basename>.insel   — INSEL model, usually containing one or more PLOT blocks
    * <basename>.gnuplot — gnuplot script with $placeholder$ substitution

    PLOT blocks write data to Insel.plot_path (insel.gpl, insel2.gpl, …).
    The gnuplot script reads those files and writes its final output
    (PNG, SVG, text, …) to wherever its `set output` directive points.

    Both files share the same **parameters for placeholder substitution.
    """

    # TODO: Should work with standard gnuplot files too, straight from VSEIT

    def __init__(self, template_path, **parameters) -> None:
        super().__init__(template_path, **parameters)
        self.gnuplot_path = self.template_full_path().with_suffix(EXT)

    def run(self) -> Union[float, Row, Table]:
        result = super().run()
        self._plot()
        return result

    def add_defaults_to(self, parameters):
        """Adds plot_folder and result_folder on top of Template's defaults.

        plot_folder:   where the gnuplot script writes its output (default: plots/ in CWD)
        result_folder: where PLOT blocks write their .gpl data files (Insel.plot_path)
        """
        parameters = super().add_defaults_to(parameters)
        defaults = {
            "plot_folder": Path("plots/"),
            "result_folder": Insel.plot_path.as_posix(),
        }
        defaults.update(parameters)
        return defaults

    def _plot_content(self):
        with open(
            self.gnuplot_path, encoding="utf-8", errors="backslashreplace"
        ) as template:
            content = template.read()
            content = re.sub(
                Template.placeholder_pattern, self.replace_placeholders, content
            )

            content = re.sub(
                r"~/(insel\d*.gpl)", rf"{self.parameters['result_folder']}/\1", content
            )

            return content

    def _temp_gnuplot(self):
        return tempfile.NamedTemporaryFile(
            mode="w+", suffix=EXT, prefix=f"{self.name}_", delete=False, encoding='utf-8',
        )

    def _plot(self):
        try:
            with self._temp_gnuplot() as temp_plot:
                temp_path = temp_plot.name
                temp_plot.write(self._plot_content())
            return subprocess.check_output([COMMAND, temp_path], shell=False)
        finally:
            os.remove(temp_path)
