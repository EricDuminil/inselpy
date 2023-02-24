from .model import Model
import tempfile
import os
from .insel import Insel


# NOTE: Abstract class
class TemporaryModel(Model):
    def tempfile(self):
        return tempfile.NamedTemporaryFile(
            mode='w+', suffix=Insel.extension, prefix='python_%s_' % self.name,
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
            "Implement %s.content() !" % self.__class__.__name__)

