from typing import Union
from .template import Template
from .model import Row, Table


class Plot(Template):
    """Insel Template + Gnuplot Template"""

    def run(self) -> Union[float, Row, Table]:
        result = super().run()
        print("Should run gnuplot now")
        return result
