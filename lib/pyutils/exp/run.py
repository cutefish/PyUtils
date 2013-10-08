import os
import re
import shutil
import shlex
import sys
import subprocess
import time

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.execute import CmdObject, runCommands
from pyutils.common.parse import CustomArgsParser, RangeStringParser

class ProjCmd(CmdObject):
    def __init__(self, command, path):
        CmdObject.__init__(self, command)
        self.path = path
        self.outfile = None
        self.errfile = None

    @property
    def cmd(self):
        return '%s 1>%s, 2>%s'%(self.command, self.outfile, self.errfile)

    def startup(self):
        self.outfile = '%s/stdout'%self.path
        self.errfile = '%s/stderr'%self.path
        self.stdout = open(self.outfile, 'w')
        self.stderr = open(self.errfile, 'w')

    def cleanup(self):
        self.stdout.close()
        self.stderr.close()
        if self.retcode == 0:
            fh = open('%s/__success__'%self.path, 'w')
            fh.write('%s'%self.retcode)
            fh.close()
        else:
            try:
                os.remove('%s/__success__'%self.path)
            except:
                pass


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
        commands.append(ProjCmd(command, path))
    runCommands(commands, numProcs)

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
        "time.sleep(5); print time.asctime(time.localtime()); print '@path'\"",
        '[1, 2, 3]', 2)
    print '===skip==='
    runProject(
        pdir,
        'python -c "import time; print time.asctime(time.localtime()); '
        "time.sleep(5); print time.asctime(time.localtime()); print '@path'\"",
        '[0:4]', 2, True)

def test():
    testRunProject()

def main():
    test()

if __name__ == '__main__':
    main()
