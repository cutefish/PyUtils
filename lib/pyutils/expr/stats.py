"""
expr.stats

Statistics Module

"""
import math
import os
import re
import sys

import pyutils.common.fileutils as fu
import pyutils.common.CliRunnable as clir
import pyutils.common.Parser as ps

def getBasics(parser, handlers):
    """
    Return count, sum, ave, std, min, max.

    Args:
        parser      -- common.Parser object to parse the files.
        handlers    -- list of file handlers.
    """
    values = []
    for h in handlers:
        for line in h:
            key, value = parser.parse(line)
            if (value != None):
                values.append(float(value))
    #count
    rcount = len(values)
    #sum
    rsum = math.fsum(values)
    #ave
    rave = rsum / rcount
    #std
    total = 0.0
    for v in values:
        total += (v - rave)**2
    rstd = math.sqrt((1.0 / (rcount - 1)) * total)
    #min and max
    rmin = values[0]
    rmax = values[0]
    for v in values:
        if v < rmin:
            rmin = v
        if v > rmax:
            rmax = v
    return rcount, rsum, rave, rstd, rmin, rmax


class StatsRunnalbe(clir.CliRunnable):

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
        parser = ps.KeyValParser(pattern)
        path = fu.normalizeName(inputPath)
        if (os.path.isdir(path)):
            fileList, sizeList = fu.listFiles(path)
        else:
            fileList = [path]

        def useFile(f, expr):
            if re.search(expr, f) != None:
                return True
            return False

        searchList = [open(f, 'r')
                      for f in fileList if useFile(f, pathFilterString)]
        rcount, rsum, rave, rstd, rmin, rmax = getBasics(parser, searchList)
        print ("cnt: " + str(rcount) + ", " +
               "sum: " + str(rsum) + ", " +
               "ave: " + str(rave) + ", " +
               "std: " + str(rstd) + ", " +
               "min: " + str(rmin) + ", " +
               "max: " + str(rmax) + ".")
