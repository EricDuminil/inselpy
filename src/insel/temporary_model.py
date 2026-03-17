import os
import tempfile
from pathlib import Path

from .insel import Insel
from .model import Model


class TemporaryModel(Model):
    """Abstract class, e.g. for OneBlockModel or Template"""

    def __init__(self, delete_after: bool = True, temp_dir: str | Path | None = None):
        super().__init__()
        self.delete_after = delete_after
        self.temp_dir = temp_dir

    def tempfile(self):
        return tempfile.NamedTemporaryFile(
            mode="w+",
            encoding="utf-8",
            suffix=Insel.extension,
            prefix=f"python_{self.name}_",
            delete=False,
            dir=self.temp_dir,
        )

    def raw_results(self) -> str:
        try:
            with self.tempfile() as temp_model:
                self.path = Path(temp_model.name)
                temp_model.write(self.content())
            return super().raw_results()
        finally:
            if self.delete_after:
                os.remove(self.path)

    def content(self) -> str:
        raise NotImplementedError(f"Implement {self.__class__.__name__}.content() !")
