import os
import subprocess
import tempfile
import re
import math
import platform
import logging
import shutil

# logging.basicConfig(level=logging.WARNING)
#TODO: Move to separate files, one per class?

class InselError(Exception):
    pass

class Insel(object):
    calls = 0

    @staticmethod
    def get_config():
        system = platform.system().lower()

        default_configs = {
            'linux': {'dirname': "/usr/local/insel/", 'command': 'insel'},
            'windows': {'dirname': os.path.join(os.getenv('ProgramFiles', ''), 'insel'), 'command': 'insel.exe'},
            'darwin': {'dirname': "/usr/local/insel/", 'command': 'insel'}
        }

        return default_configs[system]

    config = get_config.__func__()
    dirname = os.environ.get('INSEL_HOME', config['dirname'])
    command = config['command']
    if shutil.which(command) is None:
        # If insel is not in PATH, use absolute path.
        command = os.path.join(dirname, command)
    extension = ".insel"
    normal_run = re.compile(
        r'Running insel [\d\w \.\-]+ \.\.\.\s+([^\*]*)Normal end of run',
        re.I | re.DOTALL)
    warning = re.compile(r'^[EFW]\d{5}.*?$', re.M)


# NOTE: Abstract class
class Model(object):

    def __init__(self):
        self.warnings = []
        self.timeout = None
        self.path = None

    def run(self):
        raw = self.raw_results().decode()
        for problem in Insel.warning.findall(raw):
            logging.warning('INSEL : %s', problem)
            self.warnings.append(problem)
        match = Insel.normal_run.search(raw)
        if match:
            output = match.group(1)
            floats = []
            for line in output.split("\n"):
                if line:
                    values = self.parse_line(line)
                    if values is not None:
                        floats.append(values)
            return self.extract(floats)
        else:
            raise InselError("Problem with INSEL\n%s\n%s\n%s\n" %
                             ('#' * 30, raw, '#' * 30))

    def parse_line(self, line):
        if not Insel.warning.search(line):
            return self.extract([float(x) for x in line.split() if x])

    def extract(self, array):
        if len(array) == 1:
            return array[0]
        else:
            return array

    def raw_results(self):
        Insel.calls += 1
        return subprocess.check_output(
            [Insel.command, self.path], shell=False, timeout=self.timeout)


class ExistingModel(Model):
    def __init__(self, path):
        super().__init__()
        self.path = path

    def raw_results(self):
        Insel.calls += 1
        return subprocess.check_output([Insel.command, self.path], shell=False)

# NOTE: Abstract class
class TemporaryModel(Model):
    def tempfile(self):
        return tempfile.NamedTemporaryFile(
            mode='w+', suffix=Insel.extension, prefix='python_%s_' % self.name,
            delete=False)

    def raw_results(self):
        try:
            with self.tempfile() as temp_model:
                self.path = temp_model.name
                temp_model.write(self.content())
            return super().raw_results()
        finally:
            os.remove(self.path)

    def content(self):
        raise NotImplementedError("Implement %s.content() !" % self.__class__.__name__)

class OneBlockModel(TemporaryModel):
    def __init__(self, name='', inputs=[], parameters=[], outputs=1):
        super().__init__()
        self.name = name
        self.parameters = ["'%s'" % p if isinstance(p, str)
                           else str(p) for p in parameters]
        self.inputs = inputs
        self.n_in = len(inputs)
        self.n_out = outputs

    def content(self):
        lines = []
        input_ids = []
        block_id = self.n_in + 1
        screen_id = self.n_in + 2

        for i, arg in enumerate(self.inputs, 1):
            input_ids.append("%s.1" % i)
            if math.isnan(arg):
                lines.append("s %d NAN" % i)
            elif math.isinf(arg):
                lines.append("s %d INFINITY" % i)
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
    dirname = os.path.join(os.path.dirname(__file__), '../templates')
    pattern = re.compile(r'\$([\w ]+)(?:\[(\d+)\] *)?(?:\|\|([\-\w\* \.]*))?\$')

    def __init__(self, name='', **parameters):
        super().__init__()
        self.name = name
        self.parameters = self.add_defaults_to(parameters)

    def template_filename(self):
        f = os.path.join(Template.dirname, '%s.insel' % self.name)
        if os.path.exists(f):
            return f
        else:
            raise FileNotFoundError("No template in %s" % f)

    def replace(self, string):
        var_name, index, default = string.groups()
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
                'bp_folder': os.path.join(Insel.dirname, "data", "bp"),
                'data_folder': os.path.join(Template.dirname, "..", "data"),
                'template_folder': Template.dirname
                }
        defaults.update(parameters)
        return defaults

    def content(self):
        # Replace unknown chars with backslash + code, so that content can be fed to INSEL
        with open(self.template_filename(), encoding='utf-8', errors='backslashreplace') as template:
            content = template.read()
            content = re.sub(Template.pattern, self.replace, content)
            return content
