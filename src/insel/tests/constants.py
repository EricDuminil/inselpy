import platform
import contextlib
import logging
import os
from pathlib import Path
from typing import List
import insel

logging.basicConfig(level=logging.ERROR)

SCRIPT_DIR = Path(__file__).resolve().parent
IS_WINDOWS = platform.system().lower() == 'windows'
STUTTGART = [48.77, 9.18, 1]  # type: List[insel.Parameter]
IMPORTANT_BLOCKS = ['MUL', 'PI', 'PVI', 'MPP', 'DO', 'CLOCK']


@contextlib.contextmanager
def cwd(path):
    """Changes working directory and returns to previous on exit."""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)
