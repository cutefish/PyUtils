"""
cluster.ssh.py

ssh related utils.

"""
import os
import re
import shlex
import subprocess
import sys

import pyutils.common.fileutils as fu
from pyutils.common.clirunnable import CliRunnable
from pyutils.common.config import Configuration
from pyutils.common.parser import CustomArgsParser

class SSHOptions:
    """ Options of the ssh command.  """
    ENV_SSH_KEY = "SSH_OPTIONS"
    DEFAULT_SSH_KEY = "default"
    OPT_NO_STRICT_HOST_KEY_CHECKING = "-o StrictHostKeyChecking=no"
    OPT_NO_USER_KNOWN_HOSTS_FILE = "-o UserKnownHostsFile=/dev/null"

    def __init__(self, options=None, cfgFile=None):
        """ Construct the options of keys. """
        self.conf = Configuration()
        self.conf.setv(SSHOptions.DEFAULT_SSH_KEY, "")
        self.initOptions(options, cfgFile)

    def initOptions(self, options, cfgFile):
        """Find the SSH option setving.

        SSH options can be set in runtime, system environment or searched in
        config.  The overwrite priority is options > system environement >
        configuration.
        
        System env format:
            SSH_OPTIONS=[[key,]value>:]*<[key,]value>

        Configuration file format:
            key=value

        """
        if cfgFile == None:
            cfgFile = '/home/%s/.ssh/options.prop' %(os.environ['USER'])
        try:
            self.conf.addResources(cfgFile)
        except IOError:
            pass
        try:
            self.parseEnv(os.environ[SSHOptions.ENV_SSH_KEY])
        except KeyError:
            pass
        if options == None:
            return
        for key, value in options.iteritems():
            self.conf.setv(key, value)
        return

    def parseEnv(self, string):
        keyvalues = string.split(':')
        for kv in keyvalues:
            try:
                key, value = kv.split(',')
            except ValueError:
                key = SSHOptions.DEFAULT_SSH_KEY
                value = kv
            key.strip(' ')
            value.strip(' ')
            self.conf.setv(key, value)

    def setOpt(self, key, value):
        key.strip(' ')
        value.strip(' ')
        self.conf.setValue(key, value)

    def getOpt(self, target):
        option = None
        for key, value in self.conf.iteritems():
            if re.search(key, target) != None or \
               re.search(target, key) != None:
                option = value
                break
        if option == None:
            option = self.conf.getv(SSHOptions.DEFAULT_SSH_KEY)
        if option == "" or option == None:
            return ""
        return " " + option

    def iteritems(self):
        return self.conf.iteritems()

    def __str__(self):
        return str(self.conf)

class SSHCommand:
    """ SSH Command, which can be executed remotely on a node through ssh. """
    def __init__(self, user, hostname, command, options=None, 
                 stdout=sys.stdout):
        self.user = user.strip(' ')
        self.hostname = hostname.strip(' ')
        self.command = command.strip(' ')
        self.options = SSHOptions(options)
        self.stdout = stdout

    def checkOutput(self):
        """
        Run command and return its output as a byte string.

        If the return code was non-zero it rasies CalledProcessError. The
        CalledProcessError object will have the return code in the returncode
        attribute and any output in the output attribute.
        """
        shell = 'ssh%s %s@%s %s' %(self.options.getOpt(self.hostname), 
                                   self.user, self.hostname, self.command)
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
        ])

    def cmd(self, argv):
        if (len(argv) < 3):
            print
            print 'ssh cmd <user> <host-file>:<range> <command> [options]'
            print '  options:'
            print '    --conf configuration file'
            sys.exit(-1)
        self.argsParser.parse(argv)
        sshoptions = SSHOptions(cfgFile=self.argsParser.getOption('--conf'))
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
        for i in range(start, end):
            sshcmd = SSHCommand(user, allHosts[i], command, sshoptions)
            print sshcmd.checkOutput()
