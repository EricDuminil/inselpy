#!/usr/bin/env python

# Try to list every symbol of every libInsel*.so, and look for name conflicts
# Reason : TRANS was defined twice (inselBS and inselEM), which caused random SIGSEGV
# NOTE: os0txt is defined twice : either for Java or console

import subprocess
from collections import defaultdict
from pathlib import Path
from insel.insel import Insel

symbols = defaultdict(set)

for lib in Insel.dirname.glob('lib*.so'):
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
            pass
            # NOTE: Should conflicts with std also be searched?
            # symbols[line].add('std')

for (symbol, defs) in sorted(symbols.items()):
    if len(defs) > 1:
        print(symbol)
        for definition in defs:
            print("  " + definition)


