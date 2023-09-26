from pathlib import Path
from typing import Dict, Any
import re
import tempfile
from .temporary_model import TemporaryModel
from .insel import Insel


class Template(TemporaryModel):
    """
    TODO: Document
    """
    # dirname is relative to current working directory.
    # NOTE: It should not be resolved yet, because CWD might change after "import insel"
    dirname: Path = Path('templates')
    # $ placeholder_example || 1.234 $
    placeholder_pattern = re.compile(r'\$([\w ]+)(?:\[(\d+)\] *)?(?:\|\|([\-\w \.\*]*))?\$')
    # C constant_example 1.234
    constants_pattern = re.compile(r'^C\s+(\w+)\s+(["\+\-\w \.\']+)(?:% .*)?\n', re.MULTILINE)
    # PLOT and PLOT2 gnuplot filenames
    gnuplot_pattern = re.compile(r'(?:advanced_plot|insel)\.gnu')
    # Will be used to disable gnuplot
    empty_gnuplot = Path(tempfile.gettempdir()) / 'empty.gnuplot'

    def __init__(self, template_path, **parameters) -> None:
        super().__init__()
        template_path = Path(template_path)
        if template_path.suffix == '.vseit':
            self.template_path: Path = template_path
        else:
            self.template_path: Path = template_path.with_suffix('.insel')
        self.name: str = self.template_path.stem
        self.parameters: Dict[str, Any] = self.add_defaults_to(parameters)

    def template_full_path(self) -> Path:
        full_path: Path = Template.dirname.resolve() / self.template_path
        if full_path.exists():
            return full_path
        else:
            raise FileNotFoundError("No template in %s" % full_path)

    def replace_placeholders(self, match_object: re.Match) -> str:
        var_name: str
        index: str
        default: str
        var_name, index, default = match_object.groups()
        var_name = var_name.strip()
        if var_name in self.parameters:
            if index:
                try:
                    return str(self.parameters[var_name][int(index)])
                except TypeError:
                    raise AttributeError(f"'{var_name}' should be an array.")
            else:
                return str(self.parameters[var_name])
        elif default is not None:
            return default
        else:
            raise AttributeError(
                "UndefinedValue for '%s' in %s.insel template" %
                (var_name, self.name))

    def replace_constants(self, match_object: re.Match) -> str:
        var_name: str
        default: str
        var_name, default = match_object.groups()
        var_name = var_name.strip()
        if var_name in self.parameters:
            value =  repr(self.parameters[var_name])
        else:
            value = default
        return f"C {var_name} {value}"

    def disable_gnuplot(self, content):
        content, count = re.subn(Template.gnuplot_pattern, Template.empty_gnuplot.as_posix(), content)
        if count:
            with open(Template.empty_gnuplot, 'w') as tmp_gnuplot:
                tmp_gnuplot.write("exit\n")
        return content

    def add_defaults_to(self, parameters):
        defaults = {
            'bp_folder': Insel.dirname / "data" / "bp",
            'data_folder': Template.dirname.parent / "data",
            'template_folder': Template.dirname,
            'gnuplot': False
        }
        defaults.update(parameters)
        return defaults

    def content(self) -> str:
        # Replace unknown chars with backslash + code, so that content can be fed to INSEL
        with open(self.template_full_path(),
                  encoding='utf-8',
                  errors='backslashreplace') as template:
            content = template.read()
            content = re.sub(Template.constants_pattern, self.replace_constants, content)
            content = re.sub(Template.placeholder_pattern, self.replace_placeholders, content)
            if not self.parameters['gnuplot']:
                content = self.disable_gnuplot(content)
            #NOTE: Test if variable hasn't been used?
            return content
