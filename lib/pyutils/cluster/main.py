"""
cluster.main

Main entry of cluster package

"""

import sys
import CommandDict
import batchprocess

def run(argv):
    cmdDict = CommandDict.theDictonary
    try:
        module = cmdDict[argv[0]]
    except:
        print "Availabe command: ", cmdDict.keys()
        sys.exit(-1)
    module.run(argv)

