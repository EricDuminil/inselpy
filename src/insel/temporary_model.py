import tempfile
import os
from .model import Model
from .insel import Insel


class TemporaryModel(Model):
    """Abstract class, e.g. for OneBlockModel or Template"""

    def tempfile(self):
        return tempfile.NamedTemporaryFile(
            mode='w+', suffix=Insel.extension, prefix=f'python_{self.name}_',
            delete=False)

    def raw_results(self) -> bytes:
        try:
            with self.tempfile() as temp_model:
                self.path = temp_model.name
                temp_model.write(self.content())
            return super().raw_results()
        finally:
            os.remove(self.path)

    def content(self) -> str:
        raise NotImplementedError(
            f"Implement {self.__class__.__name__}.content() !")
