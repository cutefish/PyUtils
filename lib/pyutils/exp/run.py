import os
import re
import shutil
import shlex
import sys
import subprocess
import time

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.parse import CustomArgsParser
from pyutils.common.parse import RangeStringParser

def runProject(pdir, cmd, rstr, numProcs=1, skipSuccess=False):
    commands = []
    subdirs = RangeStringParser().parse(rstr)
    for sub in subdirs:
        path = '%s/%s'%(pdir, sub)
        if not os.path.isdir(path):
            raise ValueError('Path not exist: %s'%path)
        if skipSuccess and os.path.isfile('%s/__success__'%path):
            print 'skip path %s'%path
            continue
        command = re.sub('@path', path, cmd)
        commands.append((command, path))
    runCommands(commands, numProcs)

def runCommands(commands, numProcs):
    procs = []
    while True:
        #first remove processes that are finished
        for proc, path, stdout, stderr in list(procs):
            retcode = proc.poll()
            if proc.poll() is not None:
                procs.remove((proc, path, stdout, stderr))
                stdout.close()
                stderr.close()
                if retcode == 0:
                    fh = open('%s/__success__'%path, 'w')
                    fh.write('%s'%retcode)
                    fh.close()
                else:
                    try:
                        os.remove('%s/__success__'%path)
                    except:
                        pass
        #check terminate condition
        if len(procs) == 0 and len(commands) == 0:
            break
        #try to launch new commands if we can
        if len(procs) < numProcs and len(commands) != 0:
            for i in range(len(procs), numProcs):
                command, path = commands.pop()
                outfile = '%s/stdout'%path
                errfile = '%s/stderr'%path
                print command, '1>', outfile, '2>', errfile
                outfh = open(outfile, 'w')
                errfh = open(errfile, 'w')
                proc = subprocess.Popen(
                    shlex.split(command), stdout=outfh, stderr=errfh)
                procs.append((proc, path, outfh, errfh))
                if len(commands) == 0:
                    break
        time.sleep(5)

def runLoop(cmd, interval=5, timeout=sys.maxint):
    while timeout > 0:
        try:
            subprocess.call(
                shlex.split(cmd), stdout=sys.stdout, stderr=sys.stderr)
            time.sleep(interval)
            timeout -= interval
        except KeyboardInterrupt:
            print '\nKeyboardInterrupt'
            break

class RunCli(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'project': 'run project points',
            'loop' : 'loop run command',
        }

    def project(self, argv):
        parser = CustomArgsParser(optKeys=['--np'], optFlags=['--skip-success'])
        parser.parse(argv)
        if (len(parser.getPosArgs()) != 3):
            print
            print "project <project dir> <command with @path> <range ^\[[0-9,:]+\]$>"
            print "         [--np <np>, --skip-success]"
            sys.exit(-1)
        pdir = parser.getPosArg(0)
        cmd = parser.getPosArg(1)
        rstr = parser.getPosArg(2)
        np = int(parser.getOption('--np', 1))
        skip = parser.getOption('--skip-success', False)
        runProject(pdir, cmd, rstr, np, skip)

    def loop(self, argv):
        parser = CustomArgsParser(optKeys=['--interval', '--timeout'])
        parser.parse(argv)
        if (len(parser.getPosArgs()) != 1):
            print
            print "project <command> [--interval <interval>, --timeout <timeout>]"
            sys.exit(-1)
        cmd = parser.getPosArg(0)
        interval = int(parser.getOption('--interval', 5))
        timeout = int(parser.getOption('--timeout', sys.maxint))
        runLoop(cmd, interval, timeout)

##### TEST #####
def testRunProject():
    #create a project dir and config file
    pdir = '/tmp/test_runProject'
    if os.path.exists(pdir):
        shutil.rmtree(pdir)
    os.makedirs('%s/0' %pdir)
    os.makedirs('%s/1' %pdir)
    os.makedirs('%s/2' %pdir)
    os.makedirs('%s/3' %pdir)
    print '===no skip==='
    runProject(
        pdir,
        'python -c "import time; print time.asctime(time.localtime()); '
        "time.sleep(10); print time.asctime(time.localtime()); print '@path'\"",
        '[1, 2, 3]', 2)
    print '===skip==='
    runProject(
        pdir,
        'python -c "import time; print time.asctime(time.localtime()); '
        "time.sleep(10); print time.asctime(time.localtime()); print '@path'\"",
        '[0:4]', 2, True)

def test():
    testRunProject()

def main():
    test()

if __name__ == '__main__':
    main()
