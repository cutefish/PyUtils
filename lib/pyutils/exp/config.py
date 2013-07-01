import os
import re
import shutil
import sys

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.parse import CustomArgsParser

from pyutils.exp.core import *

def parseGenFile(fn):
    linecount = 0
    fh = open(fn, 'r')
    lines = []
    constsIdx = -1
    varsIdx = -1
    while True:
        line = fh.readline()
        linecount += 1
        if line == '':
            break
        line = line.strip()
        if line == '':
            continue
        if line.startswith('#consts'):
            constsIdx = len(lines)
        elif line.startswith('#vars'):
            varsIdx = len(lines)
        if line.startswith('#'):
            continue
        lines.append(line)
    cmdLine = lines[0]
    if constsIdx == -1:
        constsIdx = len(lines)
    if varsIdx == -1:
        varsIdx = len(lines)
    if constsIdx < varsIdx:
        constLines = lines[1:varsIdx]
        varLines = lines[varsIdx:]
    else:
        varLines = lines[1:constsIdx]
        constLines = lines[constsIdx:]
    return genExpPoints(cmdLine, constLines, varLines)

def parseCommandLine(argv):
    parser = CustomArgsParser(optKeys=['--consts', '--vars'])
    parser.parse(argv)
    cmdLine = parser.getPosArg(0)
    constsOption = parser.getOption('--consts')
    constLines = []
    if constsOption is not None:
        constLines.extend(constsOption.split(';'))
    varsOption = parser.getOption('--vars')
    varLines = []
    if varsOption is not None:
        varLines.extend(varsOption.split(';'))
    return genExpPoints(cmdLine, constLines, varLines)

def genExpPoints(cmdLine, constLines, varLines):
    """Generate experiment points.

    Each experiment point can be represented by a dict.
    """
    print 'command:', cmdLine
    print 'consts:', constLines
    print 'vars:', varLines
    expPoints = []
    #get the const dictionary
    consts = {}
    for line in constLines:
        key, val = line.split('=')
        key = key.strip()
        if not re.match(KEY_NAME_REGEX, key):
            raise SyntaxError('%s is not a valid key name' %key)
        val = val.strip()
        consts[key] = val
    expandValues(consts, consts)
    evaluateValues(consts)
    #get var list dictionary
    varDict = {}
    for line in varLines:
        keys, val = line.split('=')
        keys = keys.split(',')
        for i, key in enumerate(keys):
            key = key.strip()
            if not re.match(KEY_NAME_REGEX, key):
                raise SyntaxError('%s is not a valid key name' %key)
            keys[i] = key
        keys = tuple(keys)
        val = val.strip()
        varDict[keys] = val
    expandValues(varDict, consts)
    evaluateValues(varDict)
    # now we have a dictionary {(keys): [values]}
    # for example
    #   { ('k0') : [v1, v2, v3], ('k1,k2') : [(v11, v12), (v21, v22)]}
    # we want to expand it to [{key : value}]
    # i.e.
    #   [{'k0':v1, 'k1':v11, 'k2':v12}, {'k0':v1, 'k1':v11, 'k2':v12}, ...]
    varList = varDict.items()
    # varList is [((keys), [values])]
    # e.g. [(('k0'), [v1, v2, v3]), (('k1','k2'), [(v11, v12), (v21, v22)])]
    # first we calculate the total number
    total = 1
    for v in varList:
        keys, vlist = v
        total *= len(vlist)
    # generate variables
    count = 0
    currIdx = [0] * len(varList)
    while count < total:
        currDict = {}
        #fill up the dictionary of one exp points
        for idx, keysvalues in enumerate(varList):
            ktuple, vlist = keysvalues
            vtuple = vlist[currIdx[idx]]
            if not isinstance(vtuple, tuple):
                vtuple = tuple([vtuple])
            for i in range(len(ktuple)):
                currDict[ktuple[i]] = vtuple[i]
        expPoints.append(currDict)
        count += 1
        #advance index
        currIdx[0] += 1
        if currIdx[0] == len(varList[0][1]):
            currIdx[0] = 0
            for i in range(1, len(varList)):
                currIdx[i] += 1
                if currIdx[i] < len(varList[i][1]):
                    break
                currIdx[i] = 0
    #now expPoints has all the vars, update with consts and command
    for point in expPoints:
        point.update(consts)
        command = {EXP_COMMAND_KEY: cmdLine}
        expandValues(command, point)
        point.update(command)
    return expPoints

def expandValues(target, against):
    """Expand a dictionary agianst another.

    To simplify, we do not allow more than one references.
    """
    for key, val in target.iteritems():
        if not '@' in val:
            continue
        #try to replace @name with against[name]
        while '@' in val:
            match = re.search(EXPAND_NAME_REGEX, val)
            if match is None:
                raise SyntaxError('%s is not expandable' %val)
            expandName = match.group()
            expandKey = expandName.lstrip('@')
            if not expandKey in against:
                raise SyntaxError(
                    'Unknown expand name: %s. '
                    'Possibly because multi-reference is not allowed' %(expandKey))
            val = re.sub(expandName, str(against[expandKey]), val)
        target[key] = val

def evaluateValues(target):
    for key, val in target.iteritems():
        try:
            target[key] = eval(val)
        except NameError:
            #It is possible that we cannot evaluate a value because '.' is used
            #as a name seperator while python uses it as the attribute operator.
            if re.match(KEY_NAME_REGEX, val):
                continue
            else:
                raise ValueError('Cannot evaluate: %s' %val)

def writeExpPoints(projectDir, name, points):
    #we first find out how many points have been generated
    countFile = '%s/%s/%s'%(projectDir, CONFIG_DIR, CONFIG_COUNT_FILE)
    if not os.path.exists(countFile):
        fh = open(countFile, 'w')
        fh.write('0\n')
        fh.close()
    fh = open(countFile, 'r')
    count = int(fh.readline().strip())
    fh.close()
    for point in points:
        count += 1
        point[EXP_POINT_ID_KEY] = count
    fh = open(countFile, 'w')
    fh.write('%s\n'%count)
    fh.close()
    fh = open('%s/%s/%s' %(projectDir, CONFIG_DIR, name), 'w')
    for point in points:
        fh.write(EXP_POINT_CONFIG_HEADER + '\n')
        fh.write('%s = %s\n' %(EXP_COMMAND_KEY, point[EXP_COMMAND_KEY]))
        fh.write('%s = %s\n' %(EXP_POINT_ID_KEY, point[EXP_POINT_ID_KEY]))
        for key, value in point.iteritems():
            if key not in [EXP_COMMAND_KEY, EXP_POINT_ID_KEY]:
                fh.write('%s = %s\n' %(key, value))
        fh.write(EXP_POINT_CONFIG_END + '\n\n')
    fh.close()

class ConfigCli(CliRunnable):

    def __init__(self):
        self.availableCommand = {
            'command': 'configure exp point from command line',
            'genfile': 'configure exp point from generation file',
        }

    def command(self, argv):
        if (len(argv) < 3):
            print
            print 'command <project dir> <name> <command> [--consts consts, --vars vars]'
            print '  --consts   --  "k1=v1;k2=v2;k3=v3"'
            print '  --vars     --  "k1=[v1,v2,v3];k2=[w1,w2,w3]" '
            print '                 or "k1,k2=[(v1,w1),(v2,w2),(v3,w3)]'
            sys.exit(-1)
        projectDir = argv[0]
        name = argv[1]
        points = parseCommandLine(argv[2:])
        writeExpPoints(projectDir, name, points)

    def genfile(self, argv):
        if (len(argv) != 3):
            print
            print 'genfile <project dir> <name> <file>'
            sys.exit(-1)
        projectDir = argv[0]
        name = argv[1]
        points = parseGenFile(argv[2])
        writeExpPoints(projectDir, name, points)

###### TEST #####
def test():
    fileLines = [
        '#A test file for config generation\n',
        '\n',
        '#command\n',
        'python -m addThreeValues @u @v @w\n',
        '\n',
        '#consts\n',
        'x = 2\n',
        'y = 2 * @x\n',
        '\n',
        '#vars\n',
        'u = [@y, 2 * @y]\n',
        'v, w = [(2*@x, 3+@y), (3*@x, 4+@y)]\n',
    ]
    commandLine = [
        'python -m addThreeValues @u @v @w',
        '--consts',
        'x=2; y=2*@x',
        '--vars',
        'u=[@y, 2*@y]; v,w=[(2*@x, 3+@y), (3*@x, 4+@y)]',
    ]
    #first make the project directory
    projectDir = '/tmp/pyu_test_exp'
    if os.path.exists(projectDir):
        shutil.rmtree(projectDir)
    os.makedirs('%s/%s' %(projectDir, CONFIG_DIR))
    #test generation config file
    genFile = '%s/%s/testcfggen' %(projectDir, CONFIG_DIR)
    fh = open(genFile, 'w')
    fh.writelines(fileLines)
    fh.close()
    points = parseGenFile(genFile)
    writeExpPoints(projectDir, 'cfg.genfile', points)
    #test command
    points = parseCommandLine(commandLine)
    writeExpPoints(projectDir, 'cfg.command', points)

def main():
    test()

if __name__ == '__main__':
    main()
