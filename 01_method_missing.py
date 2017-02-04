#TODO: import insel. nothing more
from insel import *
from model import *
from one_block_model import *

print OneBlockModel('pi').run()
print OneBlockModel('sum', inputs = [3,2]).run()
