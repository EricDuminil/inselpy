import subprocess

from .insel import Insel
from .model import Model


class ExistingModel(Model):
    """
    Existing INSEL or Vseit models.
    Additional flags can be passed as params.
    """

    def __init__(self, *params):
        super().__init__()
        self.params = list(params)

    def raw_results(self) -> str:
        Insel.calls += 1
        return subprocess.check_output(
            [Insel.command] + self.params, shell=False
        ).decode()
