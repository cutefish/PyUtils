"""

hadoop.main

Main entry of cluster package

"""

import re
import shutil
import sys

import pyutils.common.io as cmnIO

commandList = ["addconf"]

def run(argv):
    if (argv[0] == "addconf"):
        addConf(argv[1:])
    if (argv[0] == "master"):
        setMaster(argv[1:])
    else:
        print "Available command: ", commandList

"""
Add one key value pair to configuration

Arguments:
    argv[0] --  file
    argv[1] --  key
    argv[2] --  value
"""
def addConf(argv):
    if len(argv) != 3:
        print "hadoop addconf <conf_file> <key> <value>"
        sys.exit(-1)
    confFile = cmnIO.normalizeName(argv[0])
    key = argv[1]
    value = argv[2]
    conf = open(confFile, 'r')
    tmpFile = '/tmp/pyutilTmpConf'
    tmp = open(tmpFile, 'w')
    class State:
        NotFound, Found, Modified = range(3)
    state = State.NotFound
    for line in conf:
        if state == State.Found:
            newLine = re.sub('>.*<', '>' + value + '<', line)
            tmp.write(newLine)
            state = State.Modified
            continue
        if '>' + key + '<' in line:
            state = State.Found
        #end of file
        if '/configuration' in line:
            if state == State.NotFound:
                tmp.write('<property>\n')
                tmp.write('\t<name>%s</name>\n' %key)
                tmp.write('\t<value>%s</value>\n' %value)
                tmp.write('</property>\n\n')
        tmp.write(line)
    conf.close()
    tmp.close()
    shutil.move(tmpFile, confFile)

"""
Set master

Arguments:
    argv[0] -- master file
"""
def setMaster(argv):
    if len(argv) != 2:
        print 'hadoop master <master_file> <hadoop_home>'
        sys.exit(-1)
    masterFile = cmnIO.normalizeName(argv[0])
    hadoopHome = cmnIO.normalizeName(argv[1])
    #read master file
    masterf = open(masterFile)
    master = masterf.readline().strip()
    #config
    coreSite = '%s/conf/core-site.xml' hadoopHome
    coreFSKey = 'fs.default.name'
    coreFSValue = 'hdfs://%s:9000' %master
    addConf([coreSite, coreFSKey, coreFSValue])

