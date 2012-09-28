"""
expr.main

Main entry of expr package

"""
import math
import os
import re
import sys

import pyutils.common.io as cmnio

commandList = [
    "avestd",
]

def printUsage():
    print "Availabe command: ", commandList

def run(argv):
    if len(argv) < 1:
        printUsage()
        sys.exit(-1)
    if (argv[0] == "avestd"):
        getAveStd(argv[1:])
    else:
        printUsage()


SUPPORTED_TYPES = {
    '%str' : ('.+', str, 'any string'),
    '%numstr' : ('[0-9]+', str, 'number string'),
    '%alpha' : ('[a-zA-Z]+', str, 'alphabet'),
    '%lc' : ('[a-z]+', str, 'lower case'),
    '%uc' : ('[A-Z]+', str, 'upper case'),
    '%name' : ('[a-zA-Z_-]+', str, 'regular name'),
    '%path' : ('[a-zA-Z_-/]+', str, 'path name'),
    '%int' : ('[-+0-9]+', int, 'decimal'),
    '%dec' : ('[-+0-9]+', int, 'decimal'),
    '%bin' : ('[-+01]+', int, 'binary'),
    '%oct' : ('[-+0-7]+', int, 'octal'),
    '%hex' : ('[-+0-9a-fA-F]+', int, 'hexadecimal'),
    '%float' : ('[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?', float, 'float'),
}


class LineParser:

    def __init__(self, pattern='{k:%str}\s*%:\s*{v:%str}'):
        keyPart = re.search('{k:(?P<key>.+?)}', pattern).group('key')
        valPart = re.search('{v:(?P<val>.+?)}', pattern).group('val')
        keyPattern, keyType = self.replTypeKey(keyPart)
        valPattern, valType = self.replTypeKey(valPart)
        pattern = re.sub('{k:.+?}', '(?P<key>%s)'%keyPattern, pattern)
        pattern = re.sub('{v:.+?}', '(?P<val>%s)'%valPattern, pattern)
        self.pattern = pattern
        self.keyType = keyType
        self.valType = valType

    def replTypeKey(self, pattern):
        for t in SUPPORTED_TYPES.keys():
            if t == pattern:
                return SUPPORTED_TYPES[t][0], SUPPORTED_TYPES[t][1]
        for t in SUPPORTED_TYPES.keys():
            if t in pattern:
                pattern = pattern.replace(t, SUPPORTED_TYPES[t][0])
        return pattern, str

    def parse(self, string):
        match = re.search(self.pattern, string)
        if match != None:
            key = self.keyType(match.group('key'))
            val = self.valType(match.group('val'))
            return key, val
        else:
            return None, None

    def __str__(self):
        return 'pattern:%s, keyType:%s, valType:%s' %(
            self.pattern, self.keyType, self.valType)

def getMean(values):
    size = len(values)
    total = 0.0
    for v in values:
        total += v
    return total / size

def getStd(values, mean):
    size = len(values)
    total = 0.0
    for v in values:
        total += math.sqrt((v - mean)**2)
    return math.sqrt((1.0 / (size - 1)) * (total / size))


def _getAveStd(parser, fileList):
    values = []
    for f in fileList:
        h = open(f, 'r')
        for line in h:
            key, value = parser.parse(line)
            if (value != None):
                values.append(value)
    mean = getMean(values)
    std = getStd(values, mean)
    return mean, std

def getAveStd(argv):
    if (len(argv) < 2) or (len(argv) > 3):
        print "avestd <parserString> <path> [pathFilterString]"
        print "parserString: re({v:ValueRegex})"
        sys.exit(-1)
    elif len(argv) == 2:
        parser = LineParser(argv[0])
        path = cmnio.normalizeName(argv[1])
        filterStr = '.*'
    else:
        parser = LineParser(argv[0])
        path = cmnio.normalizeName(argv[1])
        filterStr = argv[2]

    if(os.path.isdir(path)):
        fileList, sizeList = cmnio.listFiles(path)
    else:
        fileList = [path]

    def useFile(f, expr):
        if re.search(expr, f) != None:
            return True
        return False

    searchList = [f for f in fileList if useFile(f, filterStr)]
    print _getAveStd(parser, searchList)


