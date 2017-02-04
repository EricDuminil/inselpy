#TODO: import insel. nothing more
from insel import *
from model import *
from one_block_model import *

print OneBlockModel('pi').run()
print OneBlockModel('sum', inputs = [3,2]).run()
print OneBlockModel('sum', inputs = [3,2]).run()

print OneBlockModel('sin', inputs = [OneBlockModel('mul', inputs = [9, OneBlockModel('sum', inputs = [6,4]).run()]).run()]).run()
