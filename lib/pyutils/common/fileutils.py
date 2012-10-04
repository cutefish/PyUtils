"""

common.io.py

common io operation

"""

import os
import shutil

def normalizeName(fileName):
    return os.path.abspath(os.path.expanduser(fileName))

def fileToList(fileName):
    f = open(normalizeName(fileName))
    ret = []
    for line in f:
        if line.startswith("#"):
            continue
        ret.append(line.strip())
    return ret

def listToFile(fileName, ls):
    f = open(normalizeName(fileName), 'w')
    for l in ls:
        f.write(str(l) + '\n')
    f.close()

def listFiles(rootDir):
    fileList = []
    sizeList = []
    for root, subFolders, files in os.walk(rootDir):
        for f in files:
            f = os.path.abspath(os.path.join(root, f))
            fileList.append(f)
            sizeList.append(os.path.getsize(f))
    return fileList, sizeList

def replaceWith(inPath, outPath, pattern, replace, maxNumReplace=0):
    """Replace a pattern in file and return the number replaced
    Arguments:
    inPath          -- input file name
    outPath         -- output file name, can be the same with inPath
    pattern         -- regex string or compiled regex
    replace         -- replace string.
                       Use '\number' to represent group in @pattern.
    maxNumReplace   -- max number of replacement, default replace all.

    """
    inputFile = open(inPath, 'r')
    if (inPath == outPath):
        tmpPath = '/tmp/_%s_temporary' %inputPath.baseName()
    else:
        tmpPath = outPath
    outputFile = open(tmpPath, 'w')
    patternRe = re.compile(pattern)
    count = 0
    for line in inputFile:
        numMatches = len(re.findall(patternRe, line))
        #if no match write to output
        if numMatches == 0:
            outputFile.write(line)
            continue
        #if already replaced enough
        if (count >= maxNumReplace) and (maxNumReplace != 0):
            outputFile.write(line)
            continue
        if (maxNumReplace != 0):
            num = min(maxNumReplace - count, numMatches)
        else:
            num = numMatches
        outputFile.write(re.sub(patternRe, replace, line, num))
        count += num
    inputFile.close()
    outputFile.close()
    if (inPath == outPath):
        shutil.move(tmpPath, outPath)
    return count


