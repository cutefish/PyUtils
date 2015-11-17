#!/usr/bin/python2.7

import os
import shlex
import subprocess

ENV_KV_LIB_KEY = 'kv_lib'
ENV_KV_CAPACITY_KEY = 'kv_sna_capacity'
KV_LIB = os.environ[ENV_KV_LIB_KEY]
KV_JAR = '{0}/kvstore.jar'.format(KV_LIB)
KV_CAP = int(os.environ[ENV_KV_CAPACITY_KEY])
KV_ROOT = '/kvroot'

HOSTNAME = subprocess.check_output(['hostname']).strip()


def makeconfig():
    for i in range(KV_CAP):
        subprocess.check_call(
            ['mkdir', '-p', '{0}/dir{1:02d}'.format(KV_ROOT, i)])
    jcmd = ('java -Xmx256m -Xms256m -jar {jar} '
            'makebootconfig '
            '-root {path} '
            '-host {host} '
            '-port 13000 '
            '-admin 7000 '
            '-harange 13010,13020 '
            '-memory_mb 50 '
            '-store-security none '
            '-capacity {cap} '
            .format(jar=KV_JAR,
                    path=KV_ROOT,
                    host=HOSTNAME,
                    cap=KV_CAP))
    for i in range(KV_CAP):
        jcmd += '-storagedir {0}/dir{1:02d} '.format(KV_ROOT, i)
    subprocess.check_call(shlex.split(jcmd))


def startsna():
    cmd = ('java -Xmx256m -Xms256m -jar {kvjar} start -root {kvrt} '.
           format(kvjar=KV_JAR, kvrt=KV_ROOT))
    subprocess.check_call(shlex.split(cmd))


makeconfig()
startsna()
