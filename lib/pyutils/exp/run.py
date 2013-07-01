import os
import sys
import subprocess

from pyutils.common.clirunnable import CliRunnable
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
            point = {}
            while True:
                line = fh.readline()
                lineno += 1
                if line == '':
                    break
                line = line.strip()
                if re.match(EXP_POINT_CONFIG_HEADER):
                    raise SyntaxError(
                        'Configure file is corrupted at line: %s, '
                        'two consecutive header' 
                        %lineno)
                if re.match(EXP_POINT_CONFIG_END, line):
                    break
                key, val = line.split('=')
                key = key.strip()
                val = val.strip()
                point[key] = val
            points.append(point)
    return points

def runPoints(projectDir, points, lb, ub, numProcs=1):
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
                pointId = int(point[EXP_POINT_ID_KEY])
                if not (pointId >= lb and pointId <= ub):
                    continue
                command, outdir = setupPoint(point)
                outfile = '%s/stdout'%outdir
                print command, '>', outfile
                outfh = open(outfile, 'w')
                env = os.environ.copy()
                env[EXP_POINT_ID_ENV_KEY] = pointId
                env[EXP_POINT_OUT_ENV_KEY] = outdir
                proc = subprocess.Popen(command.split(' '), stdout=outfh, env=env)
                procs.append((proc, outfh))
                if len(points) == 0:
                    break
        time.sleep(10)
        print 'Points left:' %len(points)

def setupPoint(point):
    pass

class RunCli(CliRunnable):

    def __init__(self):
        self.availableCommand = {
            'run': 'run experiment points of a config file',
        }

    def repeatNIBasic(self, argv):
        if (len(argv) < 2) or (len(argv) > 3):
            print
            print "repeatNIBasic <command> <parserString> <count>"
            print
            print "  <command> experiment command string"
            print "  <parserString>: re({k:KeyRegex}, {v:ValueRegex})"
            print '    example: "{k:bandwdith}: {v:%int} MByte / s"'
            print "  <count> number of experiments"
            sys.exit(-1)
        command = argv[0]
        pattern = argv[1]
        count = int(argv[2])

        rcount, rsum, rave, rstd, rmin, rmax = repeatNoneInteract(
            command, BasicCollector(pattern), count)
        print ("cnt: " + str(rcount) + ", " +
               "sum: " + str(rsum) + ", " +
               "ave: " + str(rave) + ", " +
               "std: " + str(rstd) + ", " +
               "min: " + str(rmin) + ", " +
               "max: " + str(rmax) + ".")
