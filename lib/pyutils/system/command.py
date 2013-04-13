"""
system.command

System command utitlies
"""
import os
import getpass
import pexpect
import shlex
import subprocess
import sys
import time

from pyutils.common.clirunnable import CliRunnable

class Sudoer(object):
    """
    Sudo execute each of the command.
    """
    def __init__(self, passwd=None):
        self._passwd = passwd
        #try the passwd here
        self.execute('echo spam')

    def execute(self, command):
        child = pexpect.spawn('sudo %s' %command)
        index = child.expect(['.*(?i)password.*', pexpect.EOF])
        if index == 0:
            if self._passwd == None:
                self._passwd = getpass.getpass("sudo password:")
            child.sendline(self._passwd)
        index = child.expect(['.*(?i)password.*', pexpect.EOF])
        if index == 0:
            raise ValueError('Wrong password')

class PeriodicalExecutor(object):
    """
    Periodically execute a command.
    """
    def __init__(self, command, interval=60):
        self._command = command
        self._interval = interval

    def run(self):
        try:
            while(True):
                subprocess.call(shlex.split(self._command), 
                                stdout = sys.stdout, stderr = sys.stderr)
                time.sleep(self._interval)
        except KeyboardInterrupt:
            pass

class CommandRunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'periodexec' : 'run command periodically',
        }

    def periodexec(self, argv):
        if (len(argv) < 1):
            print
            print 'command periodexec <command> [interval]'
            print
            sys.exit(-1)
        interval = 60
        command = argv[0]
        if len(argv) > 1:
            interval = int(argv[1])
        executor = PeriodicalExecutor(command, interval)
        executor.run()

def main():
    sudoer = Sudoer()
    sudoer.execute('touch /home/xyu40/t')
    subprocess.call('ls -l /home/xyu40/t'.split(' '), stdout=sys.stdout)
    sudoer.execute('rm /home/xyu40/t')

if __name__ == '__main__':
    main()
