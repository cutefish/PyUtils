"""

common.io.py

common io operation

"""

import os

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

