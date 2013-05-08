"""
rand.py

Random utilities.
"""

import math
import random
import sys

class PoissonProcess(object):
    def __init__(self, lambd):
        self._lambd = float(lambd)
        if self._lambd <= 0:
            raise ValueError('lambda cannot be 0 for poisson process')
        random.seed();

    @property
    def lambd(self):
        return self._lambd

    @property
    def expected(self):
        return 1 / self._lambd

    def next(self):
        return -math.log(1.0 - random.random()) / self._lambd

def testPoisson(expected):
    p = PoissonProcess(1 / float(expected))
    print p.lambd
    print p.expected
    for i in range(20):
        print p.next()

def main():
    testPoisson(sys.argv[1])

if __name__ == '__main__':
    main()
    
