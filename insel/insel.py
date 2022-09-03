import os
import subprocess
import tempfile
import re
import math
import platform
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Union, Optional, Any, Sequence

# Models can return:
#  1
#  [1]
#  [[1,2],[3,4]]
#  [1,[2,3],4]
Row = List[float]
Table = List[Union[float, Row]]
Parameter = Union[float, str]

# logging.basicConfig(level=logging.WARNING)
# TODO: Move to separate files, one per class?

def get_config():
    system = platform.system().lower()

    default_configs = {
        'linux': {'dirname': "/usr/local/insel/", 'command': 'insel'},
        'windows': {'dirname': Path(os.getenv('ProgramFiles', '')) / 'insel', 'command': 'insel.exe'},
        'darwin': {'dirname': "/usr/local/insel/", 'command': 'insel'}
    }

    return default_configs[system]


class InselError(Exception):
    pass


class Insel(object):
    calls: int = 0
    config = get_config()
    dirname: Path = Path(os.environ.get('INSEL_HOME', config['dirname']))
    command = config['command']
    if shutil.which(command) is None:
        # If insel is not in PATH, use absolute path.
        command = dirname / command
    extension = ".insel"
    normal_run = re.compile(
        r'Running insel [\d\w \.\-]+ \.\.\.\s+([^\*]*)Normal end of run',
        re.I | re.DOTALL)
    warning = re.compile(r'^[EFW]\d{5}.*?$', re.M)
    # Contains warnings during last execution. Might be convenient for testing. Not thread-safe!
    last_warnings: List[str] = []
    last_raw_output: Optional[str]


# NOTE: Abstract class
class Model(object):

    def __init__(self) -> None:
        self.warnings: List[str] = []
        Insel.last_raw_output: Optional[str] = None
        Insel.last_warnings = self.warnings
        self.timeout: Optional[int] = None
        self.path: Path
        self.name: str

    def run(self) -> Union[float, Row, Table]:
        raw: str = self.raw_results().decode()
        Insel.last_raw_output = raw
        problem: str
        for problem in Insel.warning.findall(raw):
            logging.warning('INSEL : %s', problem)
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
            raise InselError("Problem with INSEL\n%s\n%s\n%s\n" %
                             ('#' * 30, raw, '#' * 30))

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

    def raw_results(self) -> bytes:
        Insel.calls += 1
        return subprocess.check_output(
            [Insel.command, self.path], shell=False, timeout=self.timeout)


class ExistingModel(Model):
    def __init__(self, *params):
        super().__init__()
        self.params = list(params)

    def raw_results(self) -> bytes:
        Insel.calls += 1
        return subprocess.check_output([Insel.command] + self.params,
                                       shell=False)


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


class OneBlockModel(TemporaryModel):
    def __init__(self, name: str = '', inputs: Sequence[float] = [], parameters : List[Parameter] = [], outputs: int = 1):
        super().__init__()
        self.name = name
        self.parameters: List[str] = ["'%s'" % p if isinstance(p, str)
                           else str(p) for p in parameters]
        self.inputs: Sequence[float] = inputs
        self.n_in: int = len(inputs)
        self.n_out: int = outputs

    def content(self) -> str:
        lines: List[str] = []
        input_ids: List[str] = []
        block_id: int = self.n_in + 1
        screen_id: int = self.n_in + 2

        for i, arg in enumerate(self.inputs, 1):
            input_ids.append("%s.1" % i)
            if math.isnan(arg):
                lines.append("s %d NAN" % i)
            elif math.isinf(arg):
                if arg > 0:
                    lines.append("s %d INFINITY" % i)
                else:
                    lines.append("s %d INFINITY" % (1000 + i))
                    lines.append("s %d CHS %d" % (i, 1000 + i))
            else:
                lines.append("s %d CONST" % i)
                lines.append("p %d" % i)
                lines.append("\t%r" % arg)

        lines.append("s %d %s %s" %
                     (block_id, self.name.upper(), " ".join(input_ids)))
        if self.parameters:
            lines.append("p %d %s" % (block_id, " ".join(self.parameters)))

        lines.append(("s %d SCREEN " % screen_id) +
                     ' '.join("%d.%d" % (block_id, i + 1) for i in range(self.n_out)))

        return "\n".join(lines)


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
        with open(self.template_full_path(), encoding='utf-8', errors='backslashreplace') as template:
            content = template.read()
            content = re.sub(Template.pattern, self.replace, content)
            return content
