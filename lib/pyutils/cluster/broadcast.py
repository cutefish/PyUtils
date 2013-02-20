"""
cluster.batchprocess.py

Batch process on a list of slaves

"""

import sys
import subprocess

import pyutils.common.fileutils as fu
import pyutils.common.clirunnable as clir

class BroadCastRunnable(clir.Clirunnable):
    def __init__(self):
        self.availableCommand = {
            'gather': 'Copy a dir/file to all nodes',
            'scatter': 'Copy a dir/file from all nodes',
            'bcastexec': 'SSH execute a command to all nodes',
        }

    def gather(self, argv):
        if (len(argv) < 3) or (len(argv) > 4):
            print "gather <srcDir> <slaveFile> <dstDir> [option_string]"
            print "     use quote for option_string"
            sys.exit(-1)
        srcDir = fu.normalizeName(argv[0])
        slaveList = fu.fileToList(argv[1])
        dstDir = fu.normalizeName(argv[2])
        options = ""
        if len(argv) == 4:
            options = argv[3]
            if not options.endswith(" "):
                options += " "
        for slave in slaveList:
            command = "scp %s-r %s %s:%s" %(options, srcDir, slave, dstDir)
            print command
            subprocess.call(command.split(" "))



    def scatter(self, argv):
        if (len(argv) < 3) or (len(argv) > 4):
            print "scatter <dstDir> <slaveFile> <srcDir> [option_string]"
            print "     use quote for option_string"
            sys.exit(-1)
        dstDir = fu.normalizeName(argv[0])
        slaveList = fu.fileToList(argv[1])
        srcDir = fu.normalizeName(argv[2])
        options = ""
        if len(argv) == 4:
            options = argv[3]
            if not options.endswith(" "):
                options += " "
        for slave in slaveList:
            command = "scp %s-r %s:%s %s" %(options, slave, srcDir, dstDir)
            print command
            subprocess.call(command.split(" "))

    def bcastexec(self, argv):
        if (len(argv) < 2) or (len(argv) > 4):
            print "bcastexec <slaveFile> <command> [option_string]"
            print "     use quote for option_string"
            sys.exit(-1)
        slaves = fu.fileToList(argv[0])
        command = argv[1]
        options = ""
        if len(argv) == 3:
            options = argv[2]
        for slave in slaves:
            sshcmd = "ssh %s %s %s" %(options, slave, command)
            print sshcmd
            subprocess.call(sshcmd.split(" "))
