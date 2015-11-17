#!/usr/bin/env python

def makeconfig(host, cap, cachettl):
    print 'Boot config sna'
    for i in range(cap):
        subprocess.check_call(shlex.split
                              ('mkdir -p /kvroot/dir{0:02d}'.format(i)))
    jcmd = ('java -Xmx256m -Xms256m -jar {kvjar} '
            'makebootconfig '
            '-root {kvrt} '
            '-host {host} '
            '-port 13000 '
            '-admin 7000 '
            '-harange 13010,13020 '
            '-memory_mb 50 '
            '-store-security none '
            '-capacity {cap} '
            '-dns-cachettl {ttl} '
            .format(kvjar=KV_JAR,
                    kvrt=KV_ROOT,
                    host='{0}.kv'.format(host),
                    cap=cap,
                    ttl=cachettl))
    for i in range(cap):
        jcmd += '-storagedir {0}/dir{1:02d} '.format(KV_ROOT, i)
    subprocess.check_call(shlex.split(jcmd))


def startsna():
    print 'Starting sn.'
    cmd = ('java -Xmx256m -Xms256m -jar {kvjar} start -root {kvrt} '.
           format(kvjar=KV_JAR, kvrt=KV_ROOT))
    subprocess.check_call(shlex.split(cmd))


print 'snaboot'

