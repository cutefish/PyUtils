"""
system.command

System command utitlies
"""
import os
import getpass
import pexpect
import subprocess
import sys

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

def main():
    sudoer = Sudoer()
    sudoer.execute('touch /home/xyu40/t')
    subprocess.call('ls -l /home/xyu40/t'.split(' '), stdout=sys.stdout)
    sudoer.execute('rm /home/xyu40/t')

if __name__ == '__main__':
    main()
