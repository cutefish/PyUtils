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


def generate_test_script():
    lines = [
        '\n',
        'connect store -host {0} -port 13000 '
        '-name "mystore"\n'.format(KV_SNAS[0]),
        'verify configuration\n'
        '\n',
        'put kv -key /name -value xiao\n',
        'get kv -key /name\n',
        'aggregate kv -count\n',
        '\n',
        'execute "DROP TABLE xiaotable"\n',
        'execute "CREATE TABLE xiaotable ('
        'item STRING,'
        'description STRING,',
        'count INTEGER,',
        'percentage DOUBLE,',
        'PRIMARY KEY (item)'
        ')"\n',
        'aggregate table -name xiaotable -count\n',
        'execute "SHOW TABLES"\n',
    ]
    with open('/tmp/test_script.kvs', 'w') as writer:
        for line in lines:
            writer.write(str(line))


def run_test_script():
    subprocess.call(shlex.split(
        'java -jar {kvjar} '
        'runadmin '
        '-host {host} '
        '-port 13000 '
        'load -file /tmp/test_script.kvs'
        .format(kvjar=KV_JAR, host=KV_SNAS[0])))


generate_test_script()
run_test_script()
