import platform
from pathlib import Path
from typing import List

SCRIPT_DIR = Path(__file__).resolve().parent
IS_WINDOWS = platform.system().lower() == 'windows'
STUTTGART = [48.77, 9.18, 1]  # type: List[insel.Parameter]
IMPORTANT_BLOCKS = ['MUL', 'PI', 'PVI', 'MPP', 'DO', 'CLOCK']
