"""
expr.stats

Statistics Module

"""
import math
import os
import re
import sys

import pyutils.common.clirunnable as clir
import pyutils.common.configuration as cfg
import pyutils.common.fileutils as fu
import pyutils.txtproc as tp
import tp.LocalFileFetcher as LocalFileFetcher
import tp.KeyValueEmitter as KeyValueEmitter
import tp.Reducer as Reducer
import tp.SysStdoutWriter as SysStdoutWriter

def BasicStatsReduer(Reducer):
    """
    Calculate count, sum, ave, std, min, max.

    """
    INVALID_VALUE_CORRECTION_KEY = "stats.basic.reducer.correction"
    DEFAULT_INVALID_VALUE_CORRECTION = 0
    def __init__(self, conf):
        self.correction = conf.get(INVALID_VALUE_CORRECTION_KEY,
                                   DEFAULT_INVALID_VALUE_CORRECTION,
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

class StatsRunnalbe(clir.Clirunnable):

    def __init__(self):
        self.availableCommand = {
            'basics': 'get count, sum, ave, std, min, max',
        }


    def basics(self, argv):
        if (len(argv) < 2) or (len(argv) > 3):
            print
            print "basic <parserString> <path> [pathFilterString]"
            print
            print "  <parserString>: re({k:KeyRegex}, {v:ValueRegex})"
            print '    example: "{k:bandwdith}: {v:%int} MByte / s"'
            print "  [pathFilterString]: path filter regular expression"
            print '    example: "[0-9]*"'
            sys.exit(-1)
        pattern = argv[0]
        inputPath = argv[1]
        pathFilterString = '.*'
        if len(argv) == 3:
            pathFilterString = argv[2]
        path = fu.normalizeName(inputPath)
        conf = cfg.Configuration()
        conf.set(tp.MODULE_FILE_KEY, self.__module__)
        conf.set(LocalFileFetcher.INPUT_DIR_KEY, path)
        conf.set(LocalFileFetcher.INPUT_FILTER_KEY, pathFilterString)
        conf.set(tp.REDUCER_CLASS_KEY, "BasicStatsReduer")
        conf.set(KeyValueEmitter.KEYVALUE_PARSE_PATTERN_KEY, pattern)
        conf.set(tp.OUTPUT_CLASS_KEY, "pyutils.expr.txtpro")
        proc = tp.TxtProc(conf)
        proc.run()

