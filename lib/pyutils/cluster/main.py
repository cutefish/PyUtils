"""
cluster.main

Main entry of cluster package

"""

import CommandDict
import batchprocess

def run(argv):
    cmdDict = CommandDict.theDictonary
    try:
        cmdDict[argv[0]].run(argv)
    except:
        print "Availabe command: ", cmdDict.keys()
