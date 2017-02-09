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
