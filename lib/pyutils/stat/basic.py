"""
expr.main

Main entry of expr package

"""
import math
import os
import re
import sys

import pyutils.common.fileutils as fu
import pyutils.common.CliRunnable as clir
import pyutils.common.Parser as ps

class StatBasicRunnalbe(clir.CliRunnable):

    def printUsage(self):
        print
        print "basic <parserString> <path> [pathFilterString]"
        print
        print "  <parserString>: re({k:KeyRegex}, {v:ValueRegex})"
        print '    example: "{k:bandwdith}: {v:%int} MByte / s"'
        print "  [pathFilterString]: path filter regular expression"
        print '    example: "[0-9]*"'

    def run(self, argv):
        if (len(argv) < 2) or (len(argv) > 3):
            self.printUsage()
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

        searchList = [f for f in fileList if useFile(f, pathFilterString)]
        values = self._getValues(parser, searchList)
        rcount = len(values)
        rsum = math.fsum(values)
        rave = rsum / rcount
        rstd = self._getStd(values, rave)
        rmin = self._getMin(values)
        rmax = self._getMax(values)
        print ("cnt: " + str(rcount) + ", " +
               "sum: " + str(rsum) + ", " +
               "ave: " + str(rave) + ", " +
               "std: " + str(rstd) + ", " +
               "min: " + str(rmin) + ", " +
               "max: " + str(rmax) + ".")

    def _getValues(self, parser, fileList):
        values = []
        for f in fileList:
            h = open(f, 'r')
            for line in h:
                key, value = parser.parse(line)
                if (value != None):
                    values.append(float(value))
        return values

    def _getStd(self, values, mean):
        size = len(values)
        total = 0.0
        for v in values:
            total += math.sqrt((v - mean)**2)
            return math.sqrt((1.0 / (size - 1)) * (total / size))

    def _getMin(self, values):
        m = values[0]
        for v in values:
            if v < m:
                m = v
        return m

    def _getMax(self, values):
        m = values[0]
        for v in values:
            if v > m:
                m = v
        return m

