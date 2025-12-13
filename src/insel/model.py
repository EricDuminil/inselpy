import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Union

from .insel import Insel
from .insel_error import InselError

Row = List[float]
Table = List[Union[float, Row]]


class Model(object):
    """Abstract class

    describes a runnable INSEL model. Its content can be generated dynamically,
    read from a file, or modified from a template."""

    def __init__(self) -> None:
        self.warnings: List[str] = []
        Insel.last_raw_output = None
        Insel.last_warnings = self.warnings
        self.timeout: Optional[int] = None
        self.path: Path
        self.name: str

    def run(self) -> Union[float, Row, Table]:
        raw = self.raw_results()
        Insel.last_raw_output = raw
        problem: str
        for problem in Insel.warning.findall(raw):
            logging.warning("INSEL : %s", problem)
            self.warnings.append(problem)
        match = Insel.normal_run.search(raw)
        if match:
            output: str = match.group(1)
            table: Table = []
            line: str
            for line in output.split("\n"):
                if line:
                    values: Optional[Union[float, List[float]]] = self.parse_line(line)
                    if values is not None:
                        table.append(values)
            return self.extract(table)
        else:
            line = "#" * 30
            raise InselError(f"Problem with INSEL\n{line}\n{raw}\n{line}\n")

    def parse_line(self, line: str) -> Optional[Union[Row, float]]:
        if Insel.warning.search(line):
            return None
        else:
            values: Row = [float(x) for x in line.split() if x]
            if len(values) == 1:
                return values[0]
            else:
                return values

    def extract(self, table: Table) -> Union[float, Row, Table]:
        if len(table) == 1:
            return table[0]
        else:
            return table

    def raw_results(self) -> str:
        Insel.calls += 1
        return subprocess.check_output(
            [Insel.command, self.path], shell=False, timeout=self.timeout
        ).decode()
