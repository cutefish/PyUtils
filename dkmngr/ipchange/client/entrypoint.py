import re
import shlex
import subprocess
import sys

KV_JAR = '/kvlib/kvstore.jar'
KV_ROOT = '/kvroot'


"""Common IP config methods. """
def config_host_ip(host):
    print 'Configuring ip for {0}'.format(host)
    interface, oldip, mask, routes = get_current_info()
    newip = get_ip(host, oldip)
    set_host_ip(newip, oldip, interface, mask, routes)
    set_etc_hosts(host, newip)
    sys.stdout.flush()


def get_current_info():
    output = subprocess.check_output(shlex.split('ifconfig'))
    interface, ip, mask = parse_ip_info(output)
    output = subprocess.check_output(shlex.split('ip route list'))
    routes = parse_routes(output)
    info = interface, ip, mask, routes
    print 'Current info: {0}'.format((info))
    return info


def parse_ip_info(output):
    lines = output.split('\n')
    intfno, addrno = find_eth_addr_line(lines)
    eth_regex = re.compile('eth[0-9]+')
    ip_regex = re.compile('inet addr:(?P<ip>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)')
    mask_regex = re.compile('Mask:(?P<mask>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)')
    try:
        interface = eth_regex.match(lines[intfno]).group()
    except:
        print 'Error in interface line: ' + lines[intfno]
        raise
    try:
        ip = ip_regex.search(lines[addrno]).group('ip')
        mask = mask_regex.search(lines[addrno]).group('mask')
    except:
        print 'Error in IP line: ' + lines[addrno]
        raise
    return interface, ip, mask


def find_eth_addr_line(lines):
    for i, line in enumerate(lines):
        line = line.strip()
        if not line.startswith('eth'):
            continue
        for j in range(i, len(lines)):
            addrline = lines[j].strip()
            if addrline.startswith('inet addr'):
                return i, j
    raise ValueError('No Ethernet IP address found.')


def parse_routes(output):
    routes = output.split('\n')
    routes = filter(lambda l : len(l) > 0, routes)
    return routes


def get_ip(host, ip):
    first, second, _, _ = ip.split('.')
    if host == 'dns':
        return '.'.join([first, second, '0', '100'])
    elif host == 'client':
        return '.'.join([first, second, '0', '200'])
    elif host.startswith('server'):
        idx = int(host[-1])
        return '.'.join([first, second, '0', '1{0}'.format(idx)])
    else:
        raise ValueError('Unknown host name.')


def set_host_ip(newip, oldip, interface, mask, routes):
    subprocess.check_call(shlex.split
                          ('ifconfig {0} down'.format(interface)))
    subprocess.check_call(shlex.split
                          ('ifconfig eth0 {0} '
                           'netmask {1} up'.format(newip, mask)))
    for route in routes:
        if oldip in route:
            continue
        subprocess.check_call(shlex.split
                              ('ip route add {0}'.format(route)))
    print 'Set new IP address.'
    subprocess.check_call(shlex.split('ifconfig'))
    subprocess.check_call(shlex.split('ip route list'))


def set_etc_hosts(host, ip):
    lines = []
    with open('/etc/hosts', 'r') as reader:
        lines.extend(reader.readlines())
    ipregex = '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'
    for i, line in enumerate(lines):
        if host in line:
            lines[i] = re.sub(ipregex, ip, line)
            print ('changed [{0}] to [{1}]\n'.
                   format(line.strip(), lines[i].strip()))
            break
    with open('/tmp/hosts', 'w') as writer:
        writer.writelines(lines)
    try:
        subprocess.check_call(shlex.split('umount /etc/hosts'))
    except:
        pass
    subprocess.check_call(shlex.split('cp /tmp/hosts /etc/hosts'))
    print 'Set new etc hosts'
    subprocess.check_call(shlex.split('cat /etc/hosts'))


"""Dns methods. """
def run_dns():
    config_host_ip('dns')
    generate_named_files()
    subprocess.check_call(shlex.split('service bind9 start'))
    subprocess.check_call(shlex.split('sleep 10000'))


def generate_named_files():
    _, ip, _, _ = get_current_info()
    first, second, _, _ = ip.strip().split('.')
    generate_named_conf_file(first, second)
    generate_named_host_file(first, second)
    generate_named_ip_file(first, second)
    sys.stdout.flush()


def generate_named_conf_file(first, second):
    prefix = '.'.join((first, second))
    reverse_prefix = '.'.join((second, first))
    lines = [
        'zone "kv" {\n',
        '    type master;\n',
        '    file "/etc/bind/db.kv";\n',
        '};\n',
        '\n',
        'zone "{0}.in-addr.arpa" {{\n'.format(reverse_prefix),
        '    type master;\n',
        '    file "/etc/bind/db.{0}";\n'.format(prefix),
        '};\n',
    ]
    with open('/etc/bind/named.conf.local', 'w') as writer:
        writer.writelines(lines)


def generate_named_host_file(first, second):
    prefix = '.'.join((first, second, '0'))
    lines = [
        ';\n',
        '; BIND data file for domain kv\n',
        ';\n',
        '$TTL    604800\n',
        '@       IN      SOA     dns.kv. admin.kv. (\n',
        '\t\t\t20150916         ; Serial\n',
        '\t\t\t604800         ; Refresh\n',
        '\t\t\t86400         ; Retry\n',
        '\t\t\t2419200         ; Expire\n',
        '\t\t\t604800 )       ; Negative Cache TTL\n',
        '\n',
        '\tIN      NS      dns.kv.\n',
        '\n',
        'dns     IN      A       {0}.100\n'.format(prefix),
        'client  IN      A       {0}.200\n'.format(prefix),
        'server0 IN      A       {0}.10\n'.format(prefix),
        'server1 IN      A       {0}.11\n'.format(prefix),
        'server2 IN      A       {0}.12\n'.format(prefix),
        'server3 IN      A       {0}.13\n'.format(prefix),
    ]
    with open('/etc/bind/db.kv', 'w') as writer:
        writer.writelines(lines)


def generate_named_ip_file(first, second):
    prefix = '.'.join((first, second))
    lines = [
        ';\n',
        '; BIND reverse data file for domain kv\n',
        ';\n',
        '$TTL    604800\n',
        '@       IN      SOA     dns.kv. admin.kv. (\n',
        '\t\t\t20150916         ; Serial\n',
        '\t\t\t604800         ; Refresh\n',
        '\t\t\t86400         ; Retry\n',
        '\t\t\t2419200         ; Expire\n',
        '\t\t\t604800 )       ; Negative Cache TTL\n',

        '\t\tIN      NS      dns.kv.\n',

        '0.100     IN      PTR     dns.kv.\n',
        '0.200     IN      PTR     client.kv.\n',
        '0.10      IN      PTR     server0.kv.\n',
        '0.11      IN      PTR     server1.kv.\n',
        '0.12      IN      PTR     server2.kv.\n',
        '0.13      IN      PTR     server3.kv.\n',
    ]
    with open('/etc/bind/db.{0}'.format(prefix), 'w') as writer:
        writer.writelines(lines)


def flip_dns(args):
    if len(args) != 1:
        print 'flip_dns <host>'
        sys.stdout.flush()
        sys.exit()
    host = args[0]
    if '.' in host:
        host = host.split('.')[0]
    _, ip, _, _ = get_current_info()
    first, second, _, _ = ip.split('.')
    prefix = '.'.join((first, second))
    generate_ns_db(host)
    generate_ip_db(host, prefix)
    subprocess.check_call(shlex.split('mv /tmp/db.kv /etc/bind/db.kv'))
    subprocess.check_call(
        shlex.split('mv /tmp/db.{0} /etc/bind/db.{0}'.format(prefix)))
    subprocess.check_call(shlex.split('service bind9 restart'))


def generate_ns_db(host):
    lines = []
    with open('/etc/bind/db.kv', 'r') as reader:
        lines.extend(reader.readlines())
    ip_regex = re.compile('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
    for i, line in enumerate(lines):
        if host in line:
            ip = re.search(ip_regex, line).group()
            ip = ipflip(ip)
            lines[i] = re.sub(ip_regex, ip, line)
            print 'Changed [{0}] to [{1}]'.format(line, lines[i])
            sys.stdout.flush()
            break
    with open('/tmp/db.kv', 'w') as writer:
        writer.writelines(lines)


def ipflip(ip):
    parts = ip.split('.')
    assert parts[2] in ['0', '1']
    if parts[2] == '0':
        parts[2] = '1'
    else:
        parts[2] = '0'
    return '.'.join(parts)


def generate_ip_db(host, prefix):
    lines = []
    with open('/etc/bind/db.{0}'.format(prefix), 'r') as reader:
        lines.extend(reader.readlines())
    for i, line in enumerate(lines):
        if host in line:
            toflip = line[0]
            assert toflip in ['0', '1']
            if toflip == '0':
                toflip = '1'
            else:
                toflip = '0'
            lines[i] = re.sub('[0-9]+', toflip, line, count=1)
            print 'Changed [{0}] to [{1}]'.format(line, lines[i])
            sys.stdout.flush()
            break
    with open('/tmp/db.{0}'.format(prefix), 'w') as writer:
        writer.writelines(lines)


"""Server methods. """
def run_server(args):
    host, cap, cachettl = parse_run_server_args(args)
    config_host_ip(host)
    makeconfig(host, cap, cachettl)
    startsna()


def parse_run_server_args(args):
    if len(args) != 3:
        print 'server <idx> <cap> <cachettl>'
        sys.exit()
    idx = int(args[0])
    cap = int(args[1])
    cachettl = int(args[2])
    return 'server{0}'.format(idx), cap, cachettl


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


def flip_ip(args):
    if len(args) != 1:
        print 'flipip <host>'
        sys.stdout.flush()
        sys.exit()
    host = args[0]
    interface, oldip, mask, routes = get_current_info()
    newip = ipflip(oldip)
    set_host_ip(newip, oldip, interface, mask, routes)
    set_etc_hosts(host, newip)
    sys.stdout.flush()


"""Client methods. """
def run_client(args):
    command, nhosts, logfine = parse_run_client_args(args)
    if nhosts < 1:
        print 'Number of hosts less than 1.'
        sys.stdout.flush()
        sys.exit()
    config_host_ip('client')
    generate_deploy_script(nhosts, logfine)
    run_deploy_script()
    subprocess.check_call(shlex.split('sleep 10000'))


def parse_run_client_args(args):
    if len(args) != 3:
        print 'client <command> <nhosts> <logfine>'
        sys.stdout.flush()
        sys.exit()
    command = args[0]
    nhosts = int(args[1])
    logfine = args[2] in ['true', 'True', 'TRUE']
    return command, nhosts, logfine


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


def main():
    if len(sys.argv) < 2:
        print 'entrypoint.py <command>'
        sys.exit()
    command = sys.argv[1]
    if command == 'dns':
        run_dns()
    if command == 'flipdns':
        flip_dns(sys.argv[2:])
    elif command == 'server':
        run_server(sys.argv[2:])
    elif command == 'flipip':
        flip_ip(sys.argv[2:])
    elif command == 'client':
        run_client(sys.argv[2:])
    elif command == 'test':
        run_test()
    else:
        print 'Unknown command: {0}'.format(command)
        sys.exit()


if __name__ == '__main__':
    main()

