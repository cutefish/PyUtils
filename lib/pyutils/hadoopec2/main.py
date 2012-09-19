"""

hadoop.main

Main entry of cluster package

"""

import re
import shutil
import sys

import boto.ec2

import pyutils.common.io as cmnIO

commandList = ["addConf",
               "master",
               "slaves",
               "startCluster",
               "startInstances",
               "stopInstances",
               "termInstances",
              ]

def printUsage():
    print "Available command: ", commandList


def run(argv):
    if len(argv) < 1:
        printUsage()
        sys.exit(-1)
    if (argv[0] == "addConf"):
        addConf(argv[1:])
    elif (argv[0] == "master"):
        setMaster(argv[1:])
    elif (argv[0] == "slaves"):
        setSlaves(argv[1:])
    elif (argv[0] == "startCluster"):
        startCluster(argv[1:])
    elif (argv[0] == "startInstances"):
        startCluster(argv[1:])
    elif (argv[0] == "stopInstances"):
        stopCluster(argv[1:])
    elif (argv[0] == "termInstances"):
        terminateCluster(argv[1:])
    else:
        printUsage()

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
Set master configurations
"""
def setMaster(argv):
    if len(argv) != 2:
        print 'hadoop master <nodeListFile> <hadoopHome>'
        sys.exit(-1)
    nodeListFile = cmnIO.normalizeName(argv[0])
    hadoopHome = cmnIO.normalizeName(argv[1])
    #read master file
    nodeList = open(nodeListFile)
    master = nodeList.readline().strip()
    #config
    coreSite = '%s/conf/core-site.xml' %hadoopHome
    coreFSKey = 'fs.default.name'
    coreFSValue = 'hdfs://%s:9000' %master
    addConf([coreSite, coreFSKey, coreFSValue])
    mprdSite = '%s/conf/mapred-site.xml' %hadoopHome
    mprdKey = 'mapred.job.tracker'
    mprdValue = 'hdfs://%s:9001' %master
    addConf([mprdSite, mprdKey, mprdValue])
    #change sync master
    tmpFile = '/tmp/hadoopenvtmp'
    envFile = '%s/conf/hadoop-env.sh' %hadoopHome
    tmp = open(tmpFile, 'w')
    env = open(envFile, 'r')
    for line in env:
        if 'HADOOP_MASTER' in line:
            tmp.write('export HADOOP_MASTER=%s:%s\n' %(master, hadoopHome))
        else:
            tmp.write(line)
    tmp.close()
    env.close()
    shutil.move(tmpFile, envFile)

"""
Set slaves file
"""
def setSlaves(argv):
    if len(argv) != 3:
        print 'hadoop slaves <nodeListFile> <hadoopHome> <numSlaves>'
        sys.exit(-1)
    nodeListFile = cmnIO.normalizeName(argv[0])
    hadoopHome = cmnIO.normalizeName(argv[1])
    numSlaves = int(argv[2])
    #read slave list
    nodeList = open(nodeListFile)
    nodeList.readline()
    slaves = []
    for line in nodeList:
        slaves.append(line.strip())
    slaves.sort()
    skip = len(slaves) / numSlaves
    #write to file
    slaveFile = open('%s/conf/slaves' %hadoopHome, 'w')
    for i in range(numSlaves):
        slaveFile.write(slaves[i * skip] + '\n')
    slaveFile.close()


"""
StartCluster
"""
def startCluster(argv):
    if len(argv) != 1:
        print "hadoop startCluster <nodeList>"
        sys.exit(-1)
    nodeList = argv[0]
    regions = boto.ec2.regions()
    regionInfo = '\n'.join(str(region).split(':')[1] for region in regions)
    regionName = raw_input("select region:\n%s\n>>"%regionInfo)
    region = boto.ec2.get_region(regionName)
    conn = region.connect()
    print "region connected successfully"
    images = conn.get_all_images(owners='self')
    imageInfo = '\n'.join(str(image).split(':')[1] for image in images)
    imageId = raw_input("enter imageId:\nself-created images:\n%s\n>>"%imageInfo)
    instanceTypeInfo = ("m1.small, " "m1.large, " "m1.xlarge\n"
                        "c1.medium, " "c1.xlarge\n"
                        "m2.xlarge, " "m2.2xlarge, " "m2.4xlarge\n"
                        "cc1.4xlarge, " "t1.micro\n")
    instanceType = raw_input("enter instanceType:\n%s\n>>"%instanceTypeInfo)
    groups = conn.get_all_security_groups()
    groupInfo = '\n'.join(str(group).split(':')[1] for group in groups)
    group = raw_input("enter securityGroup:\n%s\n>>"%groupInfo)
    keys = conn.get_all_key_pairs()
    if len(keys) == 1:
        key = keys
    else:
        keyInfo = '\n'.join(str(key).split(':')[1] for key in keys)
        key = raw_input("enter key name:\n%s\n>>"%keyInfo)
    numNodes = int(raw_input("number of nodes:\n>>"))
    reservation = conn.run_instances(
        imageId, min_count=numNodes, max_count=numNodes,
        security_groups = [group], instance_type=instanceType)
    ipList = []
    for instance in reservation.instances:
        ip = instance.public_dns_name
        if ip != "":
            ipList.append(ip)
    ipList.sort()
    cmnIO.listToFile(nodeList, ipList)
    print "First ip address: ", ipList[0]

def _getInstancesFromRegion(conn):
    resv = conn.get_all_instances()
    ret = []
    for r in resv:
        for i in resv.instances:
            ret.append(i)
    return ret

"""
startInstances
"""
def startInstances(argv):
    if len(argv) != 1:
        print "hadoop startInstances <regionName>"
        sys.exit(-1)
    regionName = argv[0]
    region = boto.ec2.get_region(regionName)
    conn = region.connect()
    instList = _getInstancesFromRegion(conn)
    startList = conn.start_instances(instList)
    print "start instances: " + startList


"""
stopInstances
"""
def stopInstances(argv):
    if len(argv) != 1:
        print "hadoop stopInstances <regionName>"
        sys.exit(-1)
    regionName = argv[0]
    region = boto.ec2.get_region(regionName)
    conn = region.connect()
    instList = _getInstancesFromRegion(conn)
    stopList = conn.stop_instances(instList)
    print "stoped instances: " + stopList

"""
termInstances
"""
def termInstances(argv):
    if len(argv) != 1:
        print "hadoop termInstances <regionName>"
        sys.exit(-1)
    regionName = argv[0]
    region = boto.ec2.get_region(regionName)
    conn = region.connect()
    instList = _getInstancesFromRegion(conn)
    termList = conn.terminate_instances(instList)
    print "terminated instances: " + termList

