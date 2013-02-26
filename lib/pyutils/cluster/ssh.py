"""
cluster.ssh.py

ssh related utils.

"""
import os
import shlex
import subprocess
import sys

import pyutils.common.fileutils as fu
from pyutils.common.clirunnable import CliRunnable
from pyutils.common.config import Configuration
from pyutils.common.parser import CustomArgsParser

class SSHOption:
    """ Options of the ssh command.  """
    DEFAULT_SSH_OPTIONS_KEY = "SSH_OPTIONS"

    OPT_NO_STRICT_HOST_KEY_CHECKING = "-o StrictHostKeyChecking=no"
    OPT_NO_USER_KNOWN_HOSTS_FILE = "-o UserKnownHostsFile=/dev/null"

    def __init__(self, args=None, conf=None, 
                 key=DEFAULT_SSH_OPTIONS_KEY):
        self.options = self.findSSHOptions(args, conf)
        self.options = self.options.strip(' ')

    def findSSHOptions(self, args, conf, 
                       key=DEFAULT_SSH_OPTIONS_KEY):
        """Find the SSH option setting.

        SSH options can be set in args, configuration or system environment.
        The overwrite priority is args > configuration > system environement.

        Returns an option string or empty string."""
        if args != None:
            return args
        ret = None
        if conf != None:
            ret = conf.get(key)
        if ret != None:
            return ret
        if os.environ[key] != None:
            return os.environ[key]
        return ""

    def addOption(self, opt):
        self.options = '%s %s' %(self.options, opt.strip(' '))

    def __str__(self):
        if self.options == "":
            return ""
        return ' %s' %self.options.strip(' ')

class SSHCommand:
    """ SSH Command, which can be executed remotely on a node through ssh. """
    def __init__(self, user, hostname, command, options=None, 
                 stdout=sys.stdout):
        self.user = user.strip(' ')
        self.hostname = hostname.strip(' ')
        self.command = command.strip(' ')
        self.options = options
        self.stdout = stdout

    def checkOutput(self):
        """
        Run command and return its output as a byte string.

        If the return code was non-zero it rasies CalledProcessError. The
        CalledProcessError object will have the return code in the returncode
        attribute and any output in the output attribute.
        """
        shell = 'ssh%s %s@%s %s' %(self.options, self.user,
                                   self.hostname, self.command)
        print 'SSHCommand: %s' %shell
        try:
            return subprocess.check_output(shlex.split(shell))
        except AttributeError:
            #A flawed patch for version < 2.7
            #if output is large, the control flow will be blocked?
            proc = subprocess.Popen(shlex.split(shell), stdout=subprocess.PIPE)
            return proc.stdout.read()

class SSHRunnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'cmd' : 'run command',
        }
        self.argsParser = CustomArgsParser([
            '--conf',
            '--option',
            '--option-key',
        ])

    def cmd(self, argv):
        if (len(argv) < 3):
            print
            print 'ssh cmd <user> <host-file>:<range> <command> [options]'
            print '  options:'
            print '    --conf configuration file'
            print '    --option ssh option string'
            print '    --option-key ssh option key'
            sys.exit(-1)
        self.argsParser.parse(argv)
        conf = Configuration()
        conf.addResources(self.argsParser.getOption('--conf'))
        options = self.argsParser.getOption('--option')
        optionKey = self.argsParser.getOption('--option-key')
        if optionKey == None:
            optionKey = SSHOption.DEFAULT_SSH_OPTIONS_KEY
        otherArgs = self.argsParser.getOtherArgs()
        user = otherArgs[0]
        hostFile, r = otherArgs[1].split(':')
        command = otherArgs[2]
        allHosts = fu.fileToList(hostFile)
        rangebound = r.split('-')
        start = int(rangebound[0])
        if len(rangebound) == 1:
            end = start + 1
        else:
            if rangebound[1] == '':
                end = len(allHosts)
            else:
                end = int(rangebound[1]) + 1
        sshopt = SSHOption(options, conf)
        for i in range(start, end):
            sshcmd = SSHCommand(user, allHosts[i], command, sshopt)
            print sshcmd.checkOutput()


def main(ip, command):
    options = SSHOption()
    options.addOption(SSHOption.OPT_NO_STRICT_HOST_KEY_CHECKING)
    options.addOption(SSHOption.OPT_NO_USER_KNOWN_HOSTS_FILE)
    options.addOption('-i /hadoop/ec2/mrioec2keypriv.pem')
    sshcmd = SSHCommand('ec2-user', ip, command, options)
    print sshcmd.checkOutput()

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

