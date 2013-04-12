"""
system.sudo

Execute sudo command.
"""
import os
import getpass
import pexpect
import subprocess
import sys

class Sudoer(object):
    """
    Sudoer objects will sudo execute each of the command.
    """
    def __init__(self, passwd=None):
        self._passwd = passwd
        self._user = os.environ['USER']
        if passwd == None:
            self._passwd = getpass.getpass("sudo password:")
        #try the passwd here
        child = pexpect.spawn('ssh echo "passwd correct"')
        child.expect('.*(?i)password.*' %self._user)
        child.sendline(self._passwd)
        #...should wait ??...


