import os
import shutil
import sys
import subprocess
import time

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.parse import CustomArgsParser
from pyutils.exp.core import *

def parseConfigFile(fn):
    fh = open(fn, 'r')
    lineno = 0
    points = []
    while True:
        line = fh.readline()
        lineno += 1
        if line == '':
            break
        #a new experiment point
        if re.match(EXP_POINT_CONFIG_HEADER, line):
            pointKeys = {}
            while True:
                line = fh.readline()
                lineno += 1
                if line == '':
                    break
                line = line.strip()
                if re.match(EXP_POINT_CONFIG_HEADER, line):
                    raise SyntaxError(
                        'Configure file is corrupted at line: %s, '
                        'two consecutive header' 
                        %lineno)
                if re.match(EXP_POINT_CONFIG_END, line):
                    break
                key, val = line.split('=')
                key = key.strip()
                val = val.strip()
                pointKeys[key] = val
            points.append(Point(pointKeys))
    return points

class AlreadyRunException(Exception):
    pass

def runPoints(projectDir, points, lb, ub, numProcs=1, skip=False):
    procs = []
    while True:
        #first remove processes that are finished
        for proc, fh in list(procs):
            if proc.poll() is not None:
                procs.remove((proc, fh))
                fh.close()
        #check terminate condition
        if len(procs) == 0 and len(points) == 0:
            break
        #try to launch new points if we can
        if len(procs) < numProcs and len(points) != 0:
            for i in range(len(procs), numProcs):
                point = points.pop()
                pointId = int(point.keys[EXP_POINT_ID_KEY])
                if not (pointId >= lb and pointId <= ub):
                    continue
                try:
                    command, outdir = setupPoint(projectDir, point, skip)
                except AlreadyRunException as e:
                    print str(e)
                    continue
                outfile = '%s/stdout'%outdir
                print command, '>', outfile
                outfh = open(outfile, 'w')
                env = os.environ.copy()
                env[EXP_POINT_ID_ENV_KEY] = str(pointId)
                env[EXP_POINT_OUT_ENV_KEY] = outdir
                proc = subprocess.Popen(command.split(' '), stdout=outfh, env=env)
                procs.append((proc, outfh))
                if len(points) == 0:
                    break
        print 'Points left:%s' %len(points)
        time.sleep(1)

def setupPoint(projectDir, point, skip):
    #make the directory
    pointId = point.keys[EXP_POINT_ID_KEY]
    runDir = '%s/%s/%s'%(projectDir, DATA_DIR, pointId)
    if os.path.exists(runDir):
        if skip:
            raise AlreadyRunException('%s already exists'%runDir)
        else:
            shutil.rmtree(runDir)
    os.makedirs(runDir)
    #write the key of the point
    keyFile = '%s/key'%(runDir)
    keyfh = open(keyFile, 'w')
    point.writeKeys(keyfh)
    return point.keys[EXP_POINT_COMMAND_KEY], runDir

class RunCli(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'run': 'run experiment points of a config file',
        }

    def run(self, argv):
        parser = CustomArgsParser(optKeys=['--np'], optFlags=['--skip'])
        parser.parse(argv)
        if (len(parser.getPosArgs()) != 3):
            print
            print "run <projectDir> <config file> <range> [--np <np>, --skip]"
            sys.exit(-1)
        projectDir = parser.getPosArg(0)
        configFile = parser.getPosArg(1)
        lb, ub = parser.getPosArg(2).split(':')
        if lb == '':
            lb = -1
        if ub == '':
            ub = sys.maxint
        lb = int(lb); ub = int(ub)
        np = int(parser.getOption('--np', 1))
        skip = parser.getOption('--skip', False)
        points = parseConfigFile(configFile)
        runPoints(projectDir, points, lb, ub, np, skip)

##### TEST #####
def test():
    #write a program
    programLines = [
        'import sys\n',
        'def main():\n',
        '   print sys.argv[1] + sys.argv[2] + sys.argv[3]\n',
        '\n',
        'if __name__ == "__main__":\n',
        '   main()\n',
    ]
    programFile = '/tmp/addThreeValues.py'
    fh = open(programFile, 'w')
    fh.writelines(programLines)
    fh.close()
    #create a project dir and config file
    projectDir = '/tmp/pyu_test_exp'
    if os.path.exists(projectDir):
        shutil.rmtree(projectDir)
    os.makedirs('%s/%s' %(projectDir, CONFIG_DIR))
    configLines = [
        '##### EXPERIMENT POINT #####\n',
        'experiment.point.command = python /tmp/addThreeValues.py 1 2 3\n',
        'experiment.point.id = 1\n',
        'u = 1\n',
        'w = 2\n',
        'v = 3\n',
        '##### END #####\n',
        '\n',
        '##### EXPERIMENT POINT #####\n',
        'experiment.point.command = python /tmp/addThreeValues.py 2 3 4\n',
        'experiment.point.id = 2\n',
        'u = 2\n',
        'w = 3\n',
        'v = 4\n',
        '##### END #####\n',
        '\n',
        '##### EXPERIMENT POINT #####\n',
        'experiment.point.command = python /tmp/addThreeValues.py 3 4 5\n',
        'experiment.point.id = 3\n',
        'u = 3\n',
        'w = 4\n',
        'v = 5\n',
        '##### END #####\n',
    ]
    configFile = '%s/%s/config' %(projectDir, CONFIG_DIR)
    fh = open(configFile, 'w')
    fh.writelines(configLines)
    fh.close()
    #now actually run
    points = parseConfigFile(configFile)
    runPoints(projectDir, points, 1, 3, 2)

def main():
    test()

if __name__ == '__main__':
    main()
