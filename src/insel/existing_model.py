import subprocess
from .model import Model
from .insel import Insel


class ExistingModel(Model):
    """
    Existing INSEL or Vseit models.
    Additional flags can be passed as params.
    """

    def __init__(self, *params):
        super().__init__()
        self.params = list(params)

    def raw_results(self) -> bytes:
        Insel.calls += 1
        return subprocess.check_output([Insel.command] + self.params,
                                       shell=False)
