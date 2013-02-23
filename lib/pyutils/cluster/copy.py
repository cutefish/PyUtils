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
from pyutils.common.parser import CustomArgsParser
from pyutils.common.parser import Parser
from pyutils.cluster.ssh import SSHOption

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


class CopyRunnable(CliRunnable):
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
        otherArgs = self.argsParser.getOtherArgs()
        user = otherArgs[0]
        src = otherArgs[1]
        dst = fu.normalizeName(otherArgs[2])
        slaveFile, r = otherArgs[3].split(':')
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
        sshoptions = SSHOption(conf=conf)
        for i in range(start, end):
            #strip the last slash of src if any, so that do not mess up the
            #destination directory.
            command = 'rsync -r -e "ssh%s" %s %s@%s:%s %s' %(
                sshoptions, filterString, 
                user, allSlaves[i], src.rstrip('/'), dst)
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
        otherArgs = self.argsParser.getOtherArgs()
        user = otherArgs[0]
        src = fu.normalizeName(otherArgs[1])
        dst = otherArgs[2]
        slaveFile, r = otherArgs[3].split(':')
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
        sshoptions = SSHOption(conf=conf)
        for i in range(start, end):
            command = 'rsync -r -e "ssh%s" %s %s %s@%s:%s' %(
                sshoptions, filterString, src, user, allSlaves[i], dst)
            print command
            subprocess.call(shlex.split(command))
