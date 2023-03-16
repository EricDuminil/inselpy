"""
Run all INSEL tests.
Alternative to:
    python -m unittest discover src/
or:
    pytest

This script should work even if insel isn't installed as a package,
while `python test_insel.py` might fail.
"""
import unittest
from pathlib import Path
SRC_DIR = Path(__file__).resolve().parent.parent.parent


def suite():
    loader = unittest.TestLoader()
    return loader.discover(SRC_DIR)


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite(), )
    # COULD DO:
    # print(f'Total INSEL calls : {Insel.calls}')
