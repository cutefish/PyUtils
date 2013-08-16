"""
cluster.copy

Copy utils for cluster. Use rsync under the hood.

"""
import os
import shlex
import shutil
import subprocess
import sys

import pyutils.common.fileutils as fu
import pyutils.common.importutils as iu
from pyutils.common.clirunnable import CliRunnable
from pyutils.common.config import Configuration
from pyutils.common.parse import CustomArgsParser
from pyutils.cluster.ssh import SSHOptions

FILTER_PATTERN_RULE_KEY = "filter.pattern.rule"
GATHER_PATTERN_RULE_KEY = "gather.pattern.rule"

class CopyPatternRule():
    def __init__(self, conf):
        pass

    def apply(self, pattern):
        if pattern == None:
            return ""
        return str(pattern)

class GatherUnderSeparateDirRule():
    """
    GatherUnderSeparateDirRule.

    Gather the copy of each host files under its own directory named by its
    hostname, e.g. /home/user/copy -> /home/user/ip1/copy.

    """
    def __init__(self, conf):
        pass

    def apply(self, src, dst, slave):
        base = os.path.basename(src.rstrip('/'))
        if (os.path.isdir(dst)):
            prefix = dst.rstrip('/')
        else:
            prefix = os.path.dirname(dst)
        olddst = prefix + "/" + base
        #if src ends with /, such as logs/, we copy the content of logs
        #equavalent to logs/* -> newdst/
        try:
            if src.endswith('/'):
                newdst = prefix + "/" + slave
            else:
                newdst = prefix + "/" + slave + "/" + base
                os.makedirs(prefix + "/" + slave)
        except OSError:
            pass
        shutil.rmtree(newdst, ignore_errors=True)
        shutil.move(olddst, newdst)
        return


class CopyCli(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'gather': 'Copy a dir/file to all nodes',
            'scatter': 'Copy a dir/file from all nodes',
        }
        self.argsParser = CustomArgsParser([
            '--conf',
            '--slaves',
            '--filter',
        ])

    def gather(self, argv):
        if (len(argv) < 4):
            print "gather <user> <src> <dst> <slave-file>:<range> [options]"
            print "  options:"
            print "    --conf configuration file"
            print "    --filter fitler pattern string"
            sys.exit(-1)
        self.argsParser.parse(argv)
        conf = Configuration()
        conf.addResources(self.argsParser.getOption('--conf'))
        filterRuleCls = conf.getClass(FILTER_PATTERN_RULE_KEY, 
                                      CopyPatternRule)
        filterRule = filterRuleCls(conf)
        filterString = filterRule.apply(
            self.argsParser.getOption('--filter'))
        gatherRuleCls = conf.getClass(GATHER_PATTERN_RULE_KEY, 
                                      GatherUnderSeparateDirRule)
        gatherRule = gatherRuleCls(conf)
        posArgs = self.argsParser.getPosArgs()
        user = posArgs[0]
        src = posArgs[1]
        dst = fu.normalizeName(posArgs[2])
        slaveFile, r = posArgs[3].split(':')
        allSlaves = fu.fileToList(slaveFile)
        rangebound = r.split('-')
        start = int(rangebound[0])
        if len(rangebound) == 1:
            end = start + 1
        else:
            if rangebound[1] == '':
                end = len(allSlaves)
            else:
                end = int(rangebound[1]) + 1
        sshoptions = SSHOptions()
        for i in range(start, end):
            #strip the last slash of src if any, so that do not mess up the
            #destination directory.
            slave = allSlaves[i]
            command = 'rsync -r -e "ssh%s" %s %s@%s:%s %s' %(
                sshoptions.getOpt(slave), filterString, 
                user, slave, src.rstrip('/'), dst)
            print command
            subprocess.call(shlex.split(command))
            #apply the gather rule
            gatherRule.apply(src, dst, allSlaves[i])

    def scatter(self, argv):
        if (len(argv) < 4):
            print "scatter <user> <src> <dst> <slave-file>:<range> [options]"
            print "  options:"
            print "    --conf configuration file"
            print "    --filter fitler pattern string"
            sys.exit(-1)
        self.argsParser.parse(argv)
        conf = Configuration()
        conf.addResources(self.argsParser.getOption('--conf'))
        filterRuleCls = conf.getClass(FILTER_PATTERN_RULE_KEY, 
                                      CopyPatternRule)
        filterRule = filterRuleCls(conf)
        filterString = filterRule.apply(
            self.argsParser.getOption('--filter'))
        posArgs = self.argsParser.getPosArgs()
        user = posArgs[0]
        src = fu.normalizeName(posArgs[1])
        dst = posArgs[2]
        slaveFile, r = posArgs[3].split(':')
        allSlaves = fu.fileToList(slaveFile)
        rangebound = r.split('-')
        start = int(rangebound[0])
        if len(rangebound) == 1:
            end = start
        else:
            if rangebound[1] == '':
                end = len(allSlaves)
            else:
                end = int(rangebound[1] + 1)
        sshoptions = SSHOptions()
        for i in range(start, end):
            slave = allSlaves[i]
            command = 'rsync -r -e "ssh%s" %s %s %s@%s:%s' %(
                sshoptions.getOpt(slave), filterString, src, user, slave, dst)
            print command
            subprocess.call(shlex.split(command))
