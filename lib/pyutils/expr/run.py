
"""
expr.run

Experiment Runnable Module

"""
import math
import os
import sys
import subprocess

import pyutils.common.parser as ps
import pyutils.common.clirunnable as clir

class ResultCollector:
    """
        ResultCollector Interface.

        Subclass define collect functions accept a file handler as parameter.
    """
    def __init__(self):
        self.result = None

    def setup(self):
        pass

    def collect(self, handler):
        raise NotImplementedError

    def cleanup(self):
        pass

def repeatNoneInteract(command, collector, count, parallel=False):
    """
    Repeat none interactive experiments and collect the result.

    Args:
        command     -- experiment system command.
        collector   -- collector object to collect the result.
        count       -- number of experiments to run.
    """
    collector.setup()
    for i in range(count):
        print 'Running experiment %s: %s' %(command, i)
        child = subprocess.Popen(command.split(' '),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT)
        collector.collect(child.stdout)
        if (not parallel):
            child.wait()
    collector.cleanup()
    return collector.result

class BasicCollector:
    def __init__(self, pattern):
        self.parser = ps.KeyValParser(pattern)

    def setup(self):
        self.values = []

    def collect(self, handler):
        for line in handler:
            key, value = self.parser.parse(line)
            if (value != None):
                self.values.append(float(value))

    def cleanup(self):
        #count
        rcount = len(self.values)
        #sum
        rsum = math.fsum(self.values)
        #ave
        rave = rsum / rcount
        #std
        total = 0.0
        for v in self.values:
            total += (v - rave)**2
            rstd = math.sqrt((1.0 / rcount) * total)
        #min and max
        rmin = self.values[0]
        rmax = self.values[0]
        for v in self.values:
            if v < rmin:
                rmin = v
            if v > rmax:
                rmax = v
        self.result = (rcount, rsum, rave,
                       rstd, rmin, rmax)

class ExprRunnalbe(clir.Clirunnable):

    def __init__(self):
        self.availableCommand = {
            'repeatNIBasic': ('repeat none interactive experiments'
                              'and collect basic statistics'),
        }

    def repeatNIBasic(self, argv):
        if (len(argv) < 2) or (len(argv) > 3):
            print
            print "repeatNIBasic <command> <parserString> <count>"
            print
            print "  <command> experiment command string"
            print "  <parserString>: re({k:KeyRegex}, {v:ValueRegex})"
            print '    example: "{k:bandwdith}: {v:%int} MByte / s"'
            print "  <count> number of experiments"
            sys.exit(-1)
        command = argv[0]
        pattern = argv[1]
        count = int(argv[2])

        rcount, rsum, rave, rstd, rmin, rmax = repeatNoneInteract(
            command, BasicCollector(pattern), count)
        print ("cnt: " + str(rcount) + ", " +
               "sum: " + str(rsum) + ", " +
               "ave: " + str(rave) + ", " +
               "std: " + str(rstd) + ", " +
               "min: " + str(rmin) + ", " +
               "max: " + str(rmax) + ".")
