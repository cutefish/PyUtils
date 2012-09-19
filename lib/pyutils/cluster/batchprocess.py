"""
cluster.batchprocess.py

Batch process on a list of slaves

"""

import sys
import pyutils.common.io as cmnIO
import subprocess

def run(argv):
    if (argv[0] == "cpToAll"):
        cpToAll(argv[1:])
    elif (argv[0] == "cpFromAll"):
        cpFromAll(argv[1:])

def cpToAll(argv):
    if len(argv) != 3:
        print "cpToAll <srcDir> <slaveFile> <dstDir>"
        sys.exit(-1)
    srcDir = cmnIO.normalizeName(argv[0])
    slaveList = cmnIO.fileToList(argv[1])
    dstDir = cmnIO.normalizeName(argv[2])
    for slave in slaveList:
        command = "scp -i /home/ec2-user/pem/HadoopExpr.pem -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -r %s %s:%s" %(srcDir, slave, dstDir)
        print command
        subprocess.call(command.split(" "))



def cpFromAll(argv):
    if len(argv) != 3:
        print "cpFromAll <dstDir> <slaveFile> <srcDir>"
        sys.exit(-1)
    pass
