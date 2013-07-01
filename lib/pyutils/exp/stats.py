"""
exp.stats

Statistics Module

"""
import math
import os
import re
import sys

import pyutils.common.fileutils as fu
import pyutils.exp.txtproc as tp
from pyutils.common.clirunnable import CliRunnable
from pyutils.common.config import Configuration
from pyutils.exp.txtproc import Reducer
from pyutils.exp.txtproc import KeyValueEmitter

class BasicStatsReduer(Reducer):
    """
    Calculate count, sum, ave, std, min, max.

    """
    INVALID_VALUE_CORRECTION_KEY = "stats.basic.reducer.correction"
    DEFAULT_INVALID_VALUE_CORRECTION = 0
    def __init__(self, conf):
        self.correction = conf.getv(self.INVALID_VALUE_CORRECTION_KEY,
                                   self.DEFAULT_INVALID_VALUE_CORRECTION,
                                   float)

    def run(self, key, values):
        valist = []
        for val in values:
            try:
                valist.append(float(val))
            except TypeError:
                valist.append(self.correction)
        rcount = len(valist)
        rsum = math.fsum(valist)
        rave = rsum / rcount
        var = 0.0
        for val in valist:
            var += (val - rave)**2
        rstd = math.sqrt((1.0 / rcount) * var)
        rmin = valist[0]
        rmax = values[0]
        for v in values:
            if v < rmin:
                rmin = v
            if v > rmax:
                rmax = v
        value = '[count=%s, sum=%s, ave=%s, std=%s, min=%s, max=%s]' %(
            rcount, rsum, rave, rstd, rmin, rmax)
        return key, value

    def __str__(self):
        return "BasicStatsReduer: " + \
                "correction= %s" % self.correction

class StatsCli(CliRunnable):

    def __init__(self):
        self.availableCommand = {
            'basics': 'get count, sum, ave, std, min, max',
        }


    def basics(self, argv):
        if (len(argv) < 2) or (len(argv) > 3):
            print
            print "basic <key/val pattern> <path> [path filter pattern]"
            print
            print "  <key/val pattern>: re({k:KeyRegex}, {v:ValueRegex})"
            print '    example: "{k:bandwdith}: {v:%int} MByte / s"'
            print "  [path filter pattern]: path filter regular expression"
            print '    example: "[0-9]*"'
            sys.exit(-1)
        pattern = argv[0]
        inputPath = argv[1]
        pathPattern = '.*'
        if len(argv) == 3:
            pathPattern = argv[2]
        path = fu.normalizeName(inputPath)
        conf = Configuration()
        conf.setv(tp.INPUT_DIR_KEY, path)
        conf.setv(tp.INPUT_FILTER_PATTERN_KEY, pathPattern)
        conf.setv(tp.REDUCER_CLASS_KEY, "pyutils.exp.stats.BasicStatsReduer")
        conf.setv(KeyValueEmitter.KEYVALUE_PARSE_PATTERN_KEY, pattern)
        conf.setv(tp.OUTPUT_CLASS_KEY, "pyutils.exp.txtproc.SysStdoutWriter")
        proc = tp.TxtProc(conf)
        print proc
        proc.run()

def main():
    obj = StatsRunnalbe()
    obj.basics()

if __name__ == '__main__':
    main()

