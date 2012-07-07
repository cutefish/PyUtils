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
    @param replace, replace string.
      Use '\number' to represent group in @pattern.
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
        Path.move(tmpPath, outPath)
    return count

def main():
    testFile = ("methods:\n"
                "void function1()\n"
                "void function2()\n"
                "void function3()\n"
                "void functionfunction4()\n"
               )
    path = Path("~/t")
    f = path.open('w')
    f.write(testFile)
    f.close()
    print replaceWith(path, path, r'(void function[0-9]+)()', r'//\1()\n\1(void)')
    print replaceWith(path, path, r'function', r'func', 7)

if __name__ == '__main__':
    main()
