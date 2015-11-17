#!/usr/bin/python2.7

import os
import shlex
import subprocess

ENV_KV_LIB_KEY = 'kv_lib'
ENV_KV_SNAS_KEY = 'kv_snas'
ENV_KV_RF_KEY = 'kv_sna_rf'
KV_LIB = os.environ[ENV_KV_LIB_KEY]
KV_JAR = '{0}/kvstore.jar'.format(KV_LIB)
KV_RF = os.environ[ENV_KV_RF_KEY]
KV_SNAS = eval(os.environ[ENV_KV_SNAS_KEY])


def generate_deploy_script():
    lines = [
        '\n',
        'configure -name "mystore"\n',
        '\n',
        'plan deploy-zone -name mydc -rf {0} -wait\n'.format(KV_RF),
        'pool create -name mypool\n',
        '\n',
        'plan deploy-sn -znname mydc -host {0} -port 13000 -wait\n'
        .format(KV_SNAS[0]),
        'pool join -name mypool -sn sn1\n',
        'plan deploy-admin -sn sn1 -port 7000 -wait\n',
        '\n',
    ]
    for i in range(1, len(KV_SNAS)):
        lines.extend([
            '\n',
            ('plan deploy-sn -znname mydc -host {0} '
             '-port 13000 -wait\n'.format(KV_SNAS[i])),
            'pool join -name mypool -sn sn{0}\n'.format(i + 1),
            'plan deploy-admin -sn sn{0} -port 7000 -wait\n'
            .format(i + 1),
            '\n',
        ])
    lines.extend([
        'topology create -name mylayout -pool mypool -partitions 100\n',
        'topology preview -name mylayout\n',
        'plan deploy-topology -name mylayout -wait\n',
        '\n',
        'show plans\n',
        'show topology\n',
        'verify configuration\n',
        '\n',
    ])
    with open('/tmp/deploy_script.kvs', 'w') as writer:
        writer.writelines(lines)


def run_deploy_script():
    cmd = ('java -Xmx256m -Xms256m -jar {kvjar} '
           'runadmin '
           '-host {host} '
           '-port 13000 '
           'load -file /tmp/deploy_script.kvs'
           .format(kvjar=KV_JAR, host=KV_SNAS[0]))
    subprocess.call(shlex.split(cmd))


generate_deploy_script()
run_deploy_script()
