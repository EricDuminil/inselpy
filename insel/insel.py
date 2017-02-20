import os
import subprocess
import tempfile
import re
import platform
import ConfigParser

class Insel:
    def get_config():
        system = platform.system().lower()

        default_configs = {
        'linux': {'dirname' : "/usr/local/INSEL/resources/", 'command': './insel'},
        'windows': {'dirname' : os.path.join(os.getenv('ProgramFiles', ''), 'INSEL 8.2', 'resources'), 'command': 'insel.exe'},
        'darwin': {'dirname' : "/Users/Shared", 'command': 'insel'}
        }

        if system == 'windows':
            ini_filename = os.path.join(os.getenv('ALLUSERSPROFILE'), 'INSEL', 'inselroot.ini')
        else:
            ini_filename = "/Users/Shared/insel/inselroot.ini"

        config = default_configs[system]

        if system == 'mac':
            subfolder = 'Contents'
        else:
            subfolder = 'resources'

        if os.path.exists(ini_filename):
            ini_file = ConfigParser.SafeConfigParser({'INSELROOT' : None})
            ini_file.read(ini_filename)
            insel_root = ini_file.get('InstallDir', 'INSELROOT')
            if insel_root:
                config['dirname'] = os.path.join(insel_root, subfolder)

        return config

    config = get_config()
    dirname = config['dirname']
    command = config['command']
    extension = ".insel"
    regexp = re.compile(
        'Running insel [\d\w \.]+ \.\.\.\s+([^\*]*)Normal end of run',
        re.I | re.DOTALL)

class Model:
    def run(self):
        raw = self.raw_results()
        match = Insel.regexp.search(raw)
        if match:
            output = match.group(1)
            floats = self.extract([self.parse_line(line)
                                   for line in output.split("\n") if line])
            os.remove(self.insel_file.name)
            return floats
        else:
            raise Exception("Problem with INSEL : %s" % raw)

    def parse_line(self, line):
        return self.extract([float(x) for x in line.split() if x])

    def extract(self, array):
        if len(array) == 1:
            return array[0]
        else:
            return array

    def raw_results(self):
        # TODO: come back to cwd
        os.chdir(Insel.dirname)
        f = self.insel_file = self.tempfile()
        f.write(self.content())
        f.close()
        return subprocess.check_output(
            [Insel.command, f.name], shell=False)

    def tempfile(self):
        return tempfile.NamedTemporaryFile(
            mode='w+', suffix=Insel.extension, prefix='python_%s_' % self.name,
            delete=False)

    def content(self):
        raise Exception("Implement %s.content() !" % self.__class__.__name__)


class OneBlockModel(Model):

    def __init__(self, name='', inputs=[], parameters=[]):
        self.name = name
        self.parameters = [
            "'%s'" %
            p if isinstance(
                p,
                basestring) else str(p) for p in parameters]
        self.inputs = inputs

    def content(self):
        lines = []
        input_ids = []
        for i, arg in enumerate(self.inputs, 1):
            input_ids.append("%s.1" % i)
            lines.append("s %d CONST" % i)
            lines.append("p %d" % i)
            lines.append("\t%r" % arg)

        lines.append(
            "s %d %s %s" %
            (len(
                self.inputs) +
                1,
                self.name.upper(),
                " ".join(input_ids)))
        lines.append(
            "p %d %s" %
            (len(
                self.inputs) +
                1,
                " ".join(
                self.parameters)))

        lines.append("s %d SCREEN %d.1" %
                     (len(self.inputs) + 2, len(self.inputs) + 1))
        return "\n".join(lines)

class Template(Model):
    dirname = os.path.join(os.path.dirname(__file__), '../templates')
    pattern = re.compile('\$([\w ]+)(?:\[(\d+)\] *)?(?:\|\|([\-\w \.]*))?\$')

    def __init__(self, name='', **parameters):
        self.name = name
        self.parameters = self.add_defaults_to(parameters)

    def template_filename(self):
        f = os.path.join(Template.dirname, '%s.insel' % self.name)
        if os.path.exists(f):
            return f
        else:
            raise Exception("No template in %s" % f)

    def replace(self, string):
        var_name, index, default = string.groups()
        var_name = var_name.strip()
        if var_name in ['longitude', 'timezone']:
            print "WARNING : Make sure to use INSEL convention for {0}. Rename to insel_{0} to remove warning".format(var_name)
        if var_name in self.parameters:
            if index:
                return str(self.parameters[var_name][int(index)])
            else:
                return str(self.parameters[var_name])
        elif default:
            return default
        else:
            raise Exception(
                "UndefinedValue for '%s' in %s.insel template" %
                (var_name, self.name))

    def add_defaults_to(self, parameters):
        defaults = {'bp_folder': os.path.join(Insel.dirname, "data", "bp")}
        if 'longitude' in parameters:
            defaults['insel_longitude'] = -parameters['longitude']
        if 'timezone' in parameters:
            defaults['insel_timezone'] = (24 - parameters['timezone']) % 24
        defaults.update(parameters)
        return defaults

    def content(self):
        with open(self.template_filename()) as template:
            content = template.read()
            content = re.sub(Template.pattern, self.replace, content)
            return content
