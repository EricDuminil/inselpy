import insel
print insel.OneBlockModel('pi').run()
print insel.OneBlockModel('sum', inputs = [3,2]).run()
#print OneBlockModel('sin', inputs = [OneBlockModel('mul', inputs = [9, OneBlockModel('sum', inputs = [6,4]).run()]).run()]).run()

print insel.Template('a_times_b', a = 5, b = 3).run()
