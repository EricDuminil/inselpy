from .temporary_model import TemporaryModel
from pathlib import Path
from typing import Dict, List, Union, Optional, Any, Sequence
import re
from .insel import Insel


class Template(TemporaryModel):
    # dirname is relative to current working directory.
    # NOTE: It should not be resolved yet, because CWD might change after "import insel"
    dirname: Path = Path('templates')
    pattern = re.compile(
        r'\$([\w ]+)(?:\[(\d+)\] *)?(?:\|\|([\-\w\* \.]*))?\$')

    def __init__(self, template_path, **parameters) -> None:
        super().__init__()
        self.template_path: Path = Path(template_path).with_suffix('.insel')
        self.name: str = self.template_path.stem
        self.parameters: Dict[str, Any] = self.add_defaults_to(parameters)

    def template_full_path(self) -> Path:
        full_path: Path = Template.dirname.resolve() / self.template_path
        if full_path.exists():
            return full_path
        else:
            raise FileNotFoundError("No template in %s" % full_path)

    def replace(self, match_object: re.Match) -> str:
        var_name: str
        index: str
        default: str
        var_name, index, default = match_object.groups()
        var_name = var_name.strip()
        if var_name in self.parameters:
            if index:
                return str(self.parameters[var_name][int(index)])
            else:
                return str(self.parameters[var_name])
        elif default is not None:
            return default
        else:
            raise AttributeError(
                "UndefinedValue for '%s' in %s.insel template" %
                (var_name, self.name))

    def add_defaults_to(self, parameters):
        defaults = {
            'bp_folder': Insel.dirname / "data" / "bp",
            'data_folder': Template.dirname.parent / "data",
            'template_folder': Template.dirname
        }
        defaults.update(parameters)
        return defaults

    def content(self) -> str:
        # Replace unknown chars with backslash + code, so that content can be fed to INSEL
        with open(self.template_full_path(),
                  encoding='utf-8',
                  errors='backslashreplace') as template:
            content = template.read()
            content = re.sub(Template.pattern, self.replace, content)
            return content
