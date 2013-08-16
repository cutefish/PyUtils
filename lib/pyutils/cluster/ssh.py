"""
cluster.ssh.py

ssh related utils.

"""
import getpass
import os
import re
import shlex
import subprocess
import sys

import pyutils.common.fileutils as fu
from pyutils.common.clirunnable import CliRunnable
from pyutils.common.parse import CustomArgsParser
from pyutils.common.parse import RangeStringParser

class SSHArgsParser(object):
    FLAG_OPTS = '1246AaCfgKkMNnqsTtVvXxYy'
    VAL_OPTS = 'bcDeFiLlmOopRSWw'
    def __init__(self):
        self.options = []
        self.posargs = []

    def parse(self, args):
        args = list(args)
        while len(args) > 0:
            arg = args.pop(0)
            if arg.startswith('-'):
                key = arg.lstrip('-')
                if key in SSHArgsParser.VAL_OPTS:
                    self.options.append(arg)
                    self.options.append(args.pop(0))
                    continue
                else:
                    valid = True
                    for k in key:
                        if k not in SSHArgsParser.FLAG_OPTS:
                            valid = False
                            break
                    if valid:
                        self.options.append(arg)
                    else:
                        raise SyntaxError('Unknown ssh option key: %s'%arg)
            else:
                self.posargs.append(arg)

def runSSHCmd(args):
    #parse the args with ssh syntax
    parser = SSHArgsParser()
    parser.parse(args)
    #parse the multi-host args
    if len(parser.posargs) != 2:
        raise SyntaxError(
            'Expect 2 positional args, got %s: %s'%(len(posargs), posargs))
    ##the first must be the hosts, the second is a command
    hosts = parser.posargs[0]
    cmd = parser.posargs[1]
    ##parse hosts
    if '@' in hosts:
        user, hosts = hosts.split('@')
    else:
        user = getpass.getuser()
    try:
        hostfile, rstr = re.split(':', hosts, 1)
    except Exception as e:
        raise SyntaxError(
            'hosts string should be in the form hostfile:range: %s'%hosts)
    hosts = fu.fileToList(hostfile)
    r = RangeStringParser().parse(rstr)
    for i in r:
        command = 'ssh %s %s@%s %s'%(' '.join(parser.options),
                                     user, hosts[i], cmd)
        print command
        subprocess.call(shlex.split(command),
                        stdout=sys.stdout, stderr=sys.stderr)

def runSSHScatter(args):
    #parse the args with ssh syntax
    parser = SSHArgsParser()
    parser.parse(args)
    #parse the multi-host args
    if len(parser.posargs) != 2:
        raise SyntaxError(
            'Expect 2 positional args, got %s: %s'%(len(posargs), posargs))
    ##the first is the src path, the second is the all hosts dst path
    src = parser.posargs[0]
    dsts = parser.posargs[1]
    ##parse hosts
    if '@' in dsts:
        user, dsts = dsts.split('@')
    else:
        user = getpass.getuser()
    try:
        hostfile, rest = re.split(':', dsts, 1)
        strlist = rest.split(':')
        if not strlist[0].startswith('['):
            raise SyntaxError('


class SSHCli(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'cmd' : 'run command',
        }

    def cmd(self, argv):
        if (len(argv) < 2):
            print
            print 'ssh cmd [<user>@]<host-file>:<range> <command> [options]'
            sys.exit(-1)
        runSSHCmd(argv)
        
