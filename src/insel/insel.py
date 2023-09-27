import platform
import shutil
from pathlib import Path
import os
import re
from typing import List, Optional, Union

# Models can return:
#  1
#  [1]
#  [[1,2],[3,4]]
#  [1,[2,3],4]
Parameter = Union[float, str]

# logging.basicConfig(level=logging.WARNING)


def get_config():
    system = platform.system().lower()

    default_configs = {
        'linux': {'dirname': "/usr/local/insel/", 'command': 'insel', 'plot_path': Path.home() / '.insel_8_3' / 'tmp'},
        'windows': {'dirname': Path(os.getenv('ProgramFiles', '')) / 'insel',
                    'plot_path': Path(os.getenv('APPDATA', '')) / 'INSEL_8_3' / 'tmp',
                    'command': 'insel.exe'},
        'darwin': {'dirname': "/usr/local/insel/", 'command': 'insel', 'plot_path': Path.home() / '.insel_8_3' / 'tmp'}
    }

    return default_configs[system]


class Insel(object):
    """Utility class, containing config, warnings and outputs"""
    calls: int = 0
    config = get_config()
    dirname: Path = Path(os.environ.get('INSEL_HOME', config['dirname']))
    plot_path: Path =  config['plot_path']
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
    last_raw_output: Optional[str] = None
