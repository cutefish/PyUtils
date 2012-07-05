"""
PyUtils.sed

sed like functions.

"""

import re
import shutil

from Path import Path

def replaceWith(inPath, outPath, pattern, replace, maxNumReplace=0):
    """Replace a pattern in file.
    @param inPath, input file path
    @param outPath, output file path, can be the same with inPath
    @param pattern, regex string or compiled regex
    @param replace, replace string
    @param maxNumReplace, max number of replacement, default replace all.

    @return number of replacement.
    """
    Path.isFileOrDie(inPath)
    inputPath = Path(inPath)
    inputFile = inputPath.open('r')
    if (inPath == outPath):
        tmpPath = '/tmp/_%s_temporary' %inputPath.baseName()
    else:
        tmpPath = outPath
    outputFile = Path(tmpPath).open('w')
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
    inputFile.close()
    outputFile.close()
    if (inPath == outPath):
        Path.move(tmpPath, outPath)
    return count

def appendLine(inPath, outPath, pattern, append, maxNumAppend=0):
    """Append after a line in file.
    @param inPath, input file path
    @param outPath, output file path, can be the same with inPath
    @param pattern, regex string or compiled regex
    @param append, append string, adding '\n' automatically
    @param maxNumAppend, max number of append, default append all.

    @return number of append.
    """
    Path.isFileOrDie(inPath)
    inputPath = Path(inPath)
    inputFile = inputPath.open('r')
    if (inPath == outPath):
        tmpPath = '/tmp/_%s_temporary' %inputPath.baseName()
    else:
        tmpPath = outPath
    outputFile = Path(tmpPath).open('w')
    regex = re.compile(pattern)
    count = 0
    lineToAppend = append + '\n'
    for line in inputFile:
        #if no match write to output
        outputFile.write(line)
        if re.search(pattern, line) == None:
            continue
        outputFile.write(lineToAppend)
        count += 1
        if count >= maxNumAppend:
            break
    inputFile.close()
    outputFile.close()
    if (inPath == outPath):
        Path.move(tmpPath, outPath)
    return count

def main():
    print appendLine("~/t", "~/t", "[0-9]+", "Hello", 3)
    #print replaceWith("~/t", "~/t", "[0-9]+", "abc", 6)

if __name__ == '__main__':
    main()
