"""

common.fileutils.py

common file operations

"""
import os
import re
import shutil
import sys

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.parse import CustomArgsParser

def normalizeName(fileName):
    return os.path.abspath(os.path.expanduser(fileName))

def fileToList(fileName, include='.*', exclude='#'):
    f = open(normalizeName(fileName))
    inclRe = re.compile(include)
    exclRe = re.compile(exclude)
    ret = []
    for line in f:
        if exclRe.search(line):
            continue
        if inclRe.search(line):
            ret.append(line.strip())
    return ret

def listToFile(fileName, ls):
    f = open(normalizeName(fileName), 'w')
    for l in ls:
        f.write(str(l) + '\n')
    f.close()

def listFiles(rootDir, topdown=True, onerror=None, 
              followlinks=False, filterstring=None):
    fileList = []
    sizeList = []
    if filterstring == None:
        filterRe = re.compile('.*')
    else:
        filterRe = re.compile(filterstring)
    for root, subFolders, files in os.walk(
        rootDir, topdown, onerror, followlinks):
        for f in files:
            try:
                f = os.path.abspath(os.path.join(root, f))
                if filterRe.search(f):
                    fileList.append(f)
                    sizeList.append(os.path.getsize(f))
            except Exception as e:
                if (ignoreError):
                    continue
                else:
                    raise e
    return fileList, sizeList

def iterFiles(rootDir, topdown=True, onerror=None, 
              followlinks=False, filterstring=None):
    if filterstring == None:
        filterRe = re.compile('.*')
    else:
        filterRe = re.compile(filterstring)
    for root, subFolders, files in os.walk(
        rootDir, topdown, onerror, followlinks):
        for f in files:
            try:
                f = os.path.abspath(os.path.join(root, f))
                if filterRe.search(f):
                    yield f, os.path.getsize(f)
            except Exception as e:
                if (ignoreError):
                    continue
                else:
                    raise e

def replace(inPath, outPath, pattern, replace, maxNumReplace=0):
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
        tmpPath = '/tmp/_%s_temporary' %os.path.basename(inPath)
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

def catFiles(rootDir, filterString='.*', out=sys.stdout):
    pattern = re.compile(filterString)
    for f, size in iterFiles(rootDir, followlinks=True):
        if pattern.search(f) != None:
            out.write('\n')
            out.write('#'*36 + ' FILE  ' + '#'*37 + '\n');
            out.write("%s\n"%f)
            out.write('#'*36 + ' START ' + '#'*37 + '\n');
            fd = open(f, 'r')
            for line in fd:
                out.write(line)
            out.write('\n')
            out.write('#'*36 + '  END  ' + '#'*37 + '\n');
            fd.close()
            
def renameFiles(rootDir, pattern, repl, verbose):
    for old in os.listdir(rootDir):
        if re.search(pattern, old):
            new = re.sub(pattern, repl, old)
            src = '%s/%s' %(rootDir, old)
            dst = '%s/%s' %(rootDir, new)
            if verbose:
                print 'Moving %s to %s' %(src, dst)
            os.rename(src, dst)

def skipUtil(fh, rexp):
    rexp = re.compile(rexp)
    while True:
        line = fh.readline()
        if line == '':
            raise EOFError
        line = line.strip()
        if rexp.search(line):
            return line

class FURunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'catfiles' : 'cat all files in a root directory',
            'rename': 'rename files(accepting regex)',
        }

    def catfiles(self, argv):
        if len(argv) == 1:
            catFiles(normalizeName(argv[0]))
        elif len(argv) == 2:
            catFiles(normalizeName(argv[0]), argv[1])
        else:
            print
            print "fileutils catfiles <root dir> [filter string]"
            sys.exit(-1)

    def rename(self, argv):
        if len(argv) < 2:
            print 
            print "fileutils rename [-v] <pattern> <repl> [root]"
            sys.exit(-1)
        argsparser = CustomArgsParser(optFlags=['-v'])
        argsparser.parse(argv)
        verbose = argsparser.getOption('-v')
        posArgs = argsparser.getPosArgs()
        pattern = posArgs[0]
        repl = posArgs[1]
        if len(posArgs) == 3:
            root = normalizeName(posArgs[2])
        else:
            root = normalizeName(os.curdir)
        renameFiles(root, pattern, repl, verbose)

