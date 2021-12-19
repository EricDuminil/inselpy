#!/usr/bin/env python

from glob import glob
import subprocess
from collections import defaultdict
from pathlib import Path

symbols = defaultdict(set)

for lib in glob('/usr/local/insel/lib*.so'):
    out = subprocess.check_output(['nm', '-gDC', '-l', lib], shell=False)
    for line in out.decode().splitlines():
        line = line[19:]
        if '\t' in line:
            name, source = line.split('\t')
            filename, linenumber = source.split(':')
            filename = Path(filename).resolve()
            source = f"{filename}:{linenumber}"
            symbols[name].add(source)
        else:
            symbols[line].add('std')


for (symbol, defs) in sorted(symbols.items()):
    if len(defs - 'std') > 1:
        print(symbol)
        for de in defs:
            print("  " + de)


