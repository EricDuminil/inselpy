from hypothesis import example, given, strategies as st # pip install hypothesis
import unittest
import math
import insel

class TestInsel(unittest.TestCase):
    """
    Basic example to show how https://hypothesis.readthedocs.io/en/latest/index.html works.
    It generates many random values, and test INSEL blocks with them:
    """
    @given(st.lists(st.floats(allow_nan=False, allow_infinity=False, width=32, max_value=1e7, min_value=-1e7), min_size=1))
    def test_sum_of_random_floats(self, xs):
        print(f"Testing {xs}")
        self.assertTrue(math.isclose(sum(xs), insel.block('sum', *xs), rel_tol=1e-5))

if __name__ == "__main__":
    unittest.main()
