"""

ec2.py

Amazon EC2 Utilities.

"""

import os
import re
import sys

import boto.ec2
from boto.ec2.blockdevicemapping import BlockDeviceType
from boto.ec2.blockdevicemapping import BlockDeviceMapping

from pyutils.common.clirunnable import CliRunnable
from pyutils.common.fileutils import fileToList, normalizeName

class EC2Runnable(CliRunnable):
    def __init__(self):
        self.availableCommand = {
            'startCluster': 'Start a ec2 cluster',
            'startInstances': 'Start instances that are previously stopped',
            'stopInstances': 'Stop instances that are currently running',
            'termInstances': 'Terminate all instances',
            'public_ips': 'print instance public IPs',
            'private_ips': 'print instance private IPs',
            'who': 'find out related instances',
        }

    def startCluster(self, argv):
        if len(argv) != 0:
            print "ec2 startCluster"
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
            key = keys[0].name
            print 'using default key: ' + key
        else:
            keyInfo = '\n'.join(str(key).split(':')[1] for key in keys)
            key = raw_input("enter key name:\n%s\n>>"%keyInfo)
        numNodes = int(raw_input("number of nodes:\n>>"))
        conn.run_instances(
            imageId, min_count=numNodes, max_count=numNodes, placement=availZone,
            security_groups = [group], instance_type=instanceType,
            block_device_map=mapping, key_name=key)

    def startInstances(self, argv):
        if len(argv) != 1:
            print "ec2 startInstances <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        instList = self._getInstancesFromRegion(conn, state='stopped')
        startList = conn.start_instances(instList)
        instInfo = ', '.join(str(i) for i in startList)
        print "start instances: " + instInfo


    def stopInstances(self, argv):
        if len(argv) != 1:
            print "ec2 stopInstances <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        instList = self._getInstancesFromRegion(conn, state='running')
        stopList = conn.stop_instances(instList)
        instInfo = ', '.join(str(i) for i in stopList)
        print "stoped instances: " + instInfo

    def termInstances(self, argv):
        if len(argv) != 1:
            print "ec2 termInstances <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        instList = self._getInstancesFromRegion(conn)
        termList = conn.terminate_instances(instList)
        instInfo = ', '.join(str(i) for i in termList)
        print "terminated instances: " + instInfo

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

    def public_ips(self, argv):
        if len(argv) < 1:
            print "ec2 public_ips <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        resvList = conn.get_all_instances()
        for resv in resvList:
            for instance in resv.instances:
                publicIp = instance.public_dns_name
                if publicIp != "" and publicIp is not None:
                    print publicIp

    def private_ips(self, argv):
        if len(argv) < 1:
            print "ec2 private_ips <regionName>"
            sys.exit(-1)
        regionName = argv[0]
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        resvList = conn.get_all_instances()
        for resv in resvList:
            for instance in resv.instances:
                privateIp = instance.private_ip_address
                if privateIp != "" and privateIp is not None:
                    print privateIp

    def who(self, argv):
        if len(argv) < 1:
            print "ec2 who <regionName> <values or path>"
            sys.exit(-1)
        regionName = argv[0]
        #get values
        valuesOrPath = argv[1]
        if os.path.isfile(normalizeName(valuesOrPath)):
            values = fileToList(valuesOrPath)
        else:
            values = valuesOrPath.split(',')
            for i in range(len(values)):
                values[i] = values[i].strip()
        #get ec2 instances
        region = boto.ec2.get_region(regionName)
        conn = region.connect()
        resvList = conn.get_all_instances()
        for value in values:
            for resv in resvList:
                for instance in resv.instances:
                    for key, val in instance.__dict__.iteritems():
                        if re.search(value, str(val)):
                            print ('value=%s: id=%s, public=%s, private=%s'
                                   %(value, instance.id,
                                     instance.ip_address,
                                     instance.private_ip_address))
                            break
