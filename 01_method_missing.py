#TODO: import insel. nothing more
from one_block_model import *
from template import *

print OneBlockModel('pi').run()
print OneBlockModel('sum', inputs = [3,2]).run()
#print OneBlockModel('sin', inputs = [OneBlockModel('mul', inputs = [9, OneBlockModel('sum', inputs = [6,4]).run()]).run()]).run()

print Template('a_times_b', a = 5, b = 3).run()
