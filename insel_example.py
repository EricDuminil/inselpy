import insel

print insel.block('pi')
print insel.block('sum', 2, 3)
print insel.block('do', parameters = [1,10,1])
print insel.template('a_times_b', a = 7, b = 3)
