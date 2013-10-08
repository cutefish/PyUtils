"""
cluster.ssh.py

ssh related utils.

"""
import getpass
import re
import subprocess
import sys
from threading import Thread

from pyutils.common.fileutils import fileToList, normalizeName
from pyutils.common.clirunnable import CliRunnable
from pyutils.common.execute import CmdObject, runCommands
from pyutils.common.parse import CustomArgsParser, RangeStringParser

class SSHArgsParser(object):
    def __init__(self, app):
        if app == 'ssh':
            self.flag_opts = '1246AaCfgKkMNnqsTtVvXxYy'
            self.val_opts = 'bcDeFiLlmOopRSWw'
        elif app == 'scp':
            self.flag_opts = '12346BCpqrv'
            self.val_opts = 'ciloFPS'
        else:
            raise ValueError('unknown app: %s'%app)
        self.app = app
        self.options = []
        self.posargs = []

    def parse(self, args):
        args = list(args)
        while len(args) > 0:
            arg = args.pop(0)
            if arg.startswith('-'):
                key = arg.lstrip('-')
                if key in self.val_opts:
                    self.options.append(arg)
                    try:
                        self.options.append(args.pop(0))
                    except IndexError:
                        raise IndexError('-%s option needs another arg' %key)
                    continue
                else:
                    valid = True
                    for k in key:
                        if k not in self.flag_opts:
                            valid = False
                            break
                    if valid:
                        self.options.append(arg)
                    else:
                        raise SyntaxError(
                            'Unknown %s option key: %s'%(self.app, arg))
            else:
                self.posargs.append(arg)


class SSHCmd(CmdObject):
    def __init__(self, command, outBufSize, errBufSize):
        CmdObject.__init__(self, command)
        self.outBuf = []
        self.errBuf = []
        self.outBufSize = 10
        self.errBufSize = 100
        self.numOutLines = 0
        self.outHandler = None
        self.errHandler = None

    def enqueueOutput(self, handler, buf, size):
        for line in iter(handler.readline, b''):
            buf.append(line)
            if handler is self.outHandler:
                self.numOutLines += 1
            #discard head lines if exceeds limit
            while len(buf) > size:
                buf.pop(0)

    def startup(self):
        self.stdout = subprocess.PIPE
        self.stderr = subprocess.PIPE

    def run(self):
        if self.outHandler is None and self.proc.stdout is not None:
            self.outHandler = self.proc.stdout
            thread = Thread(target=self.enqueueOutput,
                            args=(self.outHandler, self.outBuf, self.outBufSize))
            thread.daemon = True
            thread.start()
        if self.errHandler is None and self.proc.stderr is not None:
            self.errHandler = self.proc.stderr
            thread = Thread(target=self.enqueueOutput,
                            args=(self.errHandler, self.errBuf, self.errBufSize))
            thread.daemon = True
            thread.start()

    def cleanup(self):
        try:
            self.outHandler.close()
            self.errHandler.close()
        except:
            pass

    @property
    def output(self):
        lines = []
        lines.append('>> %s\n'%self.command)
        lines.append('stdout: %s\n'%self.numOutLines)
        for line in self.outBuf:
            lines.append(line)
        lines.append('stderr:\n')
        for line in self.errBuf:
            lines.append(line)
        lines.append('\n')
        return lines

def runSSHCmd(args, nprocs, outBufSize, errBufSize):
    #parse the args with ssh syntax
    parser = SSHArgsParser('ssh')
    parser.parse(args)
    #parse the multi-host args
    if len(parser.posargs) != 2:
        raise SyntaxError(
            'Expect 2 positional args, got %s: %s'
            %(len(parser.posargs), parser.posargs))
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
        r = RangeStringParser().parse(rstr)
    except Exception as e:
        raise SyntaxError(
            'Hosts string should be in the form hostfile:range: %s'
            'Error message: %s' %(hosts, e))
    hosts = fileToList(hostfile)
    sshCmds = []
    for i in r:
        try:
            host = hosts[i]
        except IndexError:
            print 'Host file only have %s entries'%len(hosts)
            break
        command = 'ssh %s %s@%s %s'%(' '.join(parser.options),
                                     user, host, cmd)
        sshCmds.append(SSHCmd(command, outBufSize, errBufSize))
    runCommands(sshCmds, nprocs)

def runSSHScatter(args, nprocs, outBufSize, errBufSize):
    #parse the args with ssh syntax
    parser = SSHArgsParser('scp')
    parser.parse(args)
    #parse the multi-host args
    if len(parser.posargs) != 2:
        raise SyntaxError(
            'Expect 2 positional args, got %s: %s'
            %(len(parser.posargs), parser.posargs))
    ##the first is the src path, the second is the all hosts dst path
    src = parser.posargs[0]
    dsts = parser.posargs[1]
    ##parse hosts
    if '@' in dsts:
        user, dsts = dsts.split('@')
    else:
        user = getpass.getuser()
    hostfile, r, dstdir = parseAddrString(dsts)
    hosts = fileToList(hostfile)
    src = normalizeName(src)
    dstdir = normalizeName(dstdir)
    sshCmds = []
    for i in r:
        try:
            host = hosts[i]
        except IndexError:
            print 'Host file only have %s entries'%len(hosts)
            break
        command = 'scp %s %s %s@%s:%s'%(' '.join(parser.options),
                                        src, user, host, dstdir)
        sshCmds.append(SSHCmd(command, outBufSize, errBufSize))
    runCommands(sshCmds, nprocs)

def runSSHGather(args, merge, nprocs, outBufSize, errBufSize):
    #parse the args with ssh syntax
    parser = SSHArgsParser('scp')
    parser.parse(args)
    #parse the multi-host args
    if len(parser.posargs) != 2:
        raise SyntaxError(
            'Expect 2 positional args, got %s: %s'
            %(len(parser.posargs), parser.posargs))
    #the first is the all hosts src path, the second is dst path
    srcs = parser.posargs[0]
    dst = parser.posargs[1]
    ##parse srcs
    if '@' in srcs:
        user, srcs = srcs.split('@')
    else:
        user = getpass.getuser()
    hostfile, r, srcdir = parseAddrString(srcs)
    hosts = fileToList(hostfile)
    srcdir = normalizeName(srcdir)
    dst = normalizeName(dst)
    sshCmds = []
    for i in r:
        try:
            host = hosts[i]
        except IndexError:
            print 'Host file only have %s entries'%len(hosts)
            break
        if merge:
            dstdir = dst
        else:
            dstdir = '%s/%s'%(dst, host)
        command = 'scp %s %s@%s:%s %s'%(' '.join(parser.options),
                                        user, host, srcdir, dstdir)
        sshCmds.append(SSHCmd(command, outBufSize, errBufSize))
    runCommands(sshCmds, nprocs)

def parseAddrString(address):
    try:
        hostfile, rest = re.split(':', address, 1)
        strlist = rest.split(':')
        if not strlist[0].startswith('['):
            raise SyntaxError(
                'Range string should be in the form ^\[[0-9,: ]+\]$: '%rest)
        rind = 0
        for i, string in enumerate(strlist):
            if ']' in string:
                rind = i
                break
        #insert colon between [0 : rind + 1]
        rstrlist = []
        for s in strlist[0 : rind]:
            rstrlist.append(s)
            rstrlist.append(':')
        rstrlist.append(strlist[rind])
        rstr = ''.join(rstrlist)
        r = RangeStringParser().parse(rstr)
        dstdir = ''.join(strlist[rind + 1 : ])
    except Exception as e:
        raise SyntaxError(
            'Address string %s should be in the form hostfile:rangestr:path\n'
            'Error message: %s' %(address, e))
    return hostfile, r, dstdir

class SSHCli(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'cmd' : 'run command',
            'scatter' : 'scatter local copy',
            'gather' : 'gather remote copies',
        }

    def cmd(self, argv):
        parser = CustomArgsParser(optKeys=['--np', '--outsize', '--errsize'])
        parser.parse(argv)
        if (len(parser.getPosArgs()) < 2):
            print
            print 'ssh cmd [<user>@]<host-file>:<range> <command> [options]'
            print '    options:'
            print '         --np <num procs>'
            print '         --outsize <num stdout lines>'
            print '         --errsize <num stderr lines>'
            sys.exit(-1)
        nprocs = int(parser.getOption('--np', 4))
        outBufSize = int(parser.getOption('--outsize', 10))
        errBufSize = int(parser.getOption('--errsize', 50))
        runSSHCmd(parser.getPosArgs(), nprocs, outBufSize, errBufSize)

    def scatter(self, argv):
        parser = CustomArgsParser(optKeys=['--np', '--outsize', '--errsize'])
        parser.parse(argv)
        if (len(parser.getPosArgs()) < 2):
            print
            print 'ssh scatter <src> [<user>@]<host-file>:<range>:<dst> [options]'
            print '    options:'
            print '         --np <num procs>'
            print '         --outsize <num stdout lines>'
            print '         --errsize <num stderr lines>'
            sys.exit(-1)
        nprocs = int(parser.getOption('--np', 4))
        outBufSize = int(parser.getOption('--outsize', 10))
        errBufSize = int(parser.getOption('--errsize', 50))
        runSSHScatter(parser.getPosArgs(), nprocs, outBufSize, errBufSize)

    def gather(self, argv):
        parser = CustomArgsParser(optKeys=['--np', '--outsize', '--errsize'],
                                  optFlags=['--no-merge'])
        parser.parse(argv)
        if (len(parser.getPosArgs()) < 2):
            print
            print 'ssh gather [<user>@]<host-file>:<range>:<src> <dst>'
            print '    options:'
            print '         --np <num procs>'
            print '         --outsize <num stdout lines>'
            print '         --errsize <num stderr lines>'
            print '         --no-merge'
            sys.exit(-1)
        nomerge = bool(parser.getOption('--no-merge', True))
        nprocs = int(parser.getOption('--np', 4))
        outBufSize = int(parser.getOption('--outsize', 10))
        errBufSize = int(parser.getOption('--errsize', 50))
        runSSHGather(parser.getPosArgs(), not nomerge,
                     nprocs, outBufSize, errBufSize)
