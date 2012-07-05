"""
PyUtils.sed

sed like functions.

"""

import re

import Path.Path

def replaceWith(inPath, outPath, pattern, replace, maxNumReplace=0):
    """Replace a pattern in file
    @param inPath, input file path
    @param outPath, output file path, can be the same with inPath
    @param pattern, regex string or compiled regex
    @param replace, replace string
    @param maxNumReplace, max number of replacement, default replace all.

    @return number of replacement.
    """
    Path.isFileOrDie(inPath)
    inputFile = open(inPath, 'r')
    if (inPath == outPath):
        tmpPath = '/tmp/_%s_temporary' %inPath
    else:
        tmpPath = outPath
    outputFile = open(tmpPath, 'w')
    regex = re.compile(pattern)
    count = 0
    for line in inputFile:
        numMatches = len(re.findall(regex, line))
        #if no match write to output
        if numMatches == 0:
            outputFile.write(line)
            continue
        if count < maxNumReplace:
            num = min(maxNumReplace - count, numMatches)
        else:
            num = numMatches
        outputFile.write(re.sub(regex, replace, line, num))
        count += num
        if maxNumReplace == 0:
            continue
        if count >= maxNumReplace:
            break
    return count
