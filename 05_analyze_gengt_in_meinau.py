import insel
import logging

from bisect import bisect_left

class KeyWrapper:
    def __init__(self, iterable, key):
        self.it = iterable
        self.key = key

    def __getitem__(self, i):
        return self.key(self.it[i])

    def __len__(self):
        return len(self.it)


name = 'iterations_until_gengt_convergence_in_meinau'

def has_enough_iterations(**params):
    print("Trying with %r" % params)
    logging.disable(50)
    model = insel.Template(name, **params)
    model.run()
    has_run_fine = not model.warnings
    print("  %s" % has_run_fine)
    return has_run_fine

iterations = range(100000)

deviations = [5, 4, 3, 2, 1, 0.5, 0.2, 0.1, 0.05, 0.01, 0.005]

for deviation in deviations:
    min_n = bisect_left(KeyWrapper(iterations, key= lambda n: has_enough_iterations(max_deviation = deviation,  max_iterations = n)), True)
    dev = insel.template(name, max_deviation = deviation, max_iterations = min_n)
    print('Max allowed deviation : %g°C, calculated in %d steps. Max deviation over 5 years: %.3f °C' % (deviation, min_n, dev))
