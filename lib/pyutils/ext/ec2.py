"""

hadoop.main

Main entry of cluster package

"""

import re
import shutil
import sys

import boto.ec2
from boto.ec2.blockdevicemapping import BlockDeviceType
from boto.ec2.blockdevicemapping import BlockDeviceMapping

import pyutils.common.fileutils as fu
from pyutils.common.clirunnable import CliRunnable

class EC2Runnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'startCluster': 'Start a ec2 cluster',
            'getRunningIp': ('Get the current running instance ip'
                             'and put it into /tmp/ec2P* file'),
            'startInstances': 'Start instances that are previously stopped',
            'stopInstances': 'Stop instances that are currently running',
            'termInstances': 'Terminate all instances',
        }

    #startCluster
    def startCluster(self, argv):
        if len(argv) != 0:
            print "hadoop startCluster"
            sys.exit(-1)
        regions = boto.ec2.regions()
        regionInfo = '\n'.join(str(region).split(':')[1] for region in regions)
        regionName = raw_input("select region:\n%s\n>>"%regionInfo)
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        print "region connected successfully"
        images = conn.get_all_images(owners='self')
        imageInfo = '\n'.join(
            str(image).split(':')[1] + ":" + image.name for image in images)
        imageId = raw_input("enter imageId:\nself-created images:\n%s\n>>"%imageInfo)
        instanceTypeInfo = ("m1.small, " "m1.large, " "m1.xlarge\n"
                            "c1.medium, " "c1.xlarge\n"
                            "m2.xlarge, " "m2.2xlarge, " "m2.4xlarge\n"
                            "cc1.4xlarge, " "t1.micro\n")
        instanceType = raw_input("enter instanceType:\n%s\n>>"%instanceTypeInfo)
        availZone = raw_input("enter placement[a,b,c]:\n>>")
        availZone = regionName + availZone
        diskSize = int(raw_input("enter disk size[G]:\n>>"))
        rootDev = BlockDeviceType()
        rootDev.name = 'root'
        rootDev.size = diskSize
        rootDev.delete_on_termination = True
        instStorage = bool(raw_input("mount inst storage?\n>>"))
        mapping = BlockDeviceMapping()
        mapping['/dev/sda1'] = rootDev
        if (instStorage == True):
            eph0 = BlockDeviceType()
            eph0.ephemeral_name = 'ephemeral0'
        mapping['/dev/sdb'] = eph0
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
            imageId, min_count=numNodes, max_count=numNodes, placement=availZone,
            security_groups = [group], instance_type=instanceType,
            block_device_map=mapping)

    #get running ip
    def getRunningIp(self, argv):
        if len(argv) < 1:
            print "hadoop getRunningIp <regionName> [outdir]"
            sys.exit(-1)
        regionName = argv[0]
        try:
            outdir = argv[1].rstrip('/')
        except:
            outdir = '/tmp'
        pubIpList = []
        priIpList = []
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        resvList = conn.get_all_instances()
        for resv in resvList:
            for instance in resv.instances:
                publicIp = instance.public_dns_name
                if publicIp != "":
                    pubIpList.append(publicIp)
                    privateIp = instance.private_ip_address
                    priIpList.append(privateIp)
        fu.listToFile('%s/ec2Public' %outdir, pubIpList)
        fu.listToFile('%s/ec2Private' %outdir, priIpList)
        print "Up nodes: ", len(pubIpList)
        if (len(pubIpList) != 0):
            print "First ip address: ", pubIpList[0]

    def _getInstancesFromRegion(self, conn, state=None):
        resv = conn.get_all_instances()
        ret = []
        for r in resv:
            for i in r.instances:
                if state == None:
                    ret.append(i.id)
                elif i.state == state:
                    ret.append(i.id)
        return ret

    #start instances
    def startInstances(self, argv):
        if len(argv) != 1:
            print "hadoop startInstances <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        instList = self._getInstancesFromRegion(conn, state='stopped')
        startList = conn.start_instances(instList)
        instInfo = ', '.join(str(i) for i in startList)
        print "start instances: " + instInfo


    #stop instances
    def stopInstances(self, argv):
        if len(argv) != 1:
            print "hadoop stopInstances <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        instList = self._getInstancesFromRegion(conn, state='running')
        stopList = conn.stop_instances(instList)
        instInfo = ', '.join(str(i) for i in stopList)
        print "stoped instances: " + instInfo

    #terminate instances
    def termInstances(self, argv):
        if len(argv) != 1:
            print "hadoop termInstances <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        instList = self._getInstancesFromRegion(conn)
        termList = conn.terminate_instances(instList)
        instInfo = ', '.join(str(i) for i in termList)
        print "terminated instances: " + instInfo

