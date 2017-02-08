from one_block_model import *
from template import *
import unittest
import math

class MyTest(unittest.TestCase):
    def test(self):
        self.assertAlmostEqual(OneBlockModel('pi').run(), math.pi, places=6) # WTF INSEL? single float precision

if __name__ == '__main__':
    unittest.main()

