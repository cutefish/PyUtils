#!/usr/bin/python2.7

import os
import re
import shlex
import socket
import subprocess
import sys


def config_host_ip():
    interface, oldip, mask, routes = get_current_info()
    newip = get_ip(oldip)
    set_host_ip(newip, oldip, interface, mask, routes)
    set_etc_hosts(newip)
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
    desired_ip = os.environ['host.desired.ip']
    newparts = desired_ip.split('.')
    oldparts = ip.split('.')
    parts = []
    for i, part in enumerate(newparts):
        if part == '*':
            parts.append(oldparts[i])
        else:
            parts.append(newparts[i])
    return '.'.join(parts)

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


def set_etc_hosts(ip):
    lines = []
    with open('/etc/hosts', 'r') as reader:
        lines.extend(reader.readlines())
    ipregex = '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+'
    for i, line in enumerate(lines):
        if ip in line:
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


config_host_ip()

