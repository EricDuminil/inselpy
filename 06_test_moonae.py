import insel
STUTTGART = [48.77, -9.18, 23]
SOMEWHERE = [60.0, -15, 23]

#insel.block('MOONAE', 2015, 3, 20, 9, 45, parameters=SOMEWHERE, outputs=5)
insel.block('MOONAE', 1990, 4, 19, 1, 0, parameters=SOMEWHERE, outputs=5)

# Seems okay:
# 101.833801      -16.2458096      -19.8790913       271.837219       100.109009
# TODO: Add full moon search

