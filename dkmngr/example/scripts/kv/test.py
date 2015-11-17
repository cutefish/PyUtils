#!/usr/bin/env python

def generate_deploy_script(nhosts, logfine):
    lines = [
        '\n',
        'configure -name "mystore"\n',
        '\n',
        'plan deploy-zone -name mydc -rf 3 -wait\n',
        'pool create -name mypool\n',
        '\n',
        'plan deploy-sn -znname mydc -host {0} -port 13000 -wait\n'
        .format('server0.kv'),
        'pool join -name mypool -sn sn1\n',
        'plan deploy-admin -sn sn1 -port 7000 -wait\n',
        '\n',
    ]
    if logfine:
        lines.append(
            'change-policy -params '
            'loggingConfigProps='
            '"oracle.kv.util.FileHandler.level=ALL;'
            'oracle.kv.impl.level=FINE;'
            'com.sleepycat.je.util.FileHandler.level=ALL;'
            'com.sleepycat.je.level=FINE"\n')
    for i in range(1, nhosts):
        lines.extend([
            '\n',
            ('plan deploy-sn -znname mydc -host server{0}.kv '
             '-port 13000 -wait\n'.format(i)),
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
    print 'Deploy cluster.'
    subprocess.call(shlex.split(
        'java -Xmx256m -Xms256m -jar {kvjar} '
        'runadmin '
        '-host server0.kv '
        '-port 13000 '
        'load -file /tmp/deploy_script.kvs'
        .format(kvjar=KV_JAR)))


def run_test():
    generate_test_script()
    run_test_script()


def generate_test_script():
    lines = [
        '\n',
        'connect store -host {host} -port 13000 '
        '-name "mystore"\n'.format(host='server0.kv'),
        'verify configuration\n'
        '\n',
        'put kv -key /name -value xiao\n',
        'get kv -key /name\n',
        'aggregate kv -count\n',
        '\n',
        'execute "DROP TABLE mytable"\n',
        'execute "CREATE TABLE mytable ('
        'item STRING,'
        'description STRING,',
        'count INTEGER,',
        'percentage DOUBLE,',
        'PRIMARY KEY (item)'
        ')"\n',
        'aggregate table -name mytable -count\n',
        'execute "SHOW TABLES"\n',
    ]
    with open('/tmp/test_script.kvs', 'w') as writer:
        for line in lines:
            writer.write(str(line))


def run_test_script():
    print 'Run test.'
    sys.stdout.flush()
    subprocess.call(shlex.split(
        'java -jar {kvjar} '
        'runadmin '
        '-host {host} '
        '-port 13000 '
        'load -file /tmp/test_script.kvs'
        .format(kvjar=KV_JAR, host='server0.kv')))


print 'test'
