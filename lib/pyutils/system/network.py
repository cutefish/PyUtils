"""

system network utilities

"""

import os
import socket

if os.name != "nt":
    import fcntl
    import struct

    def getInterfaceIp(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(
            fcntl.ioctl(s.fileno(), 0x8915,
                        struct.pack('256s', ifname[:15]))[20:24])

def getLocalIpAddress():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith('127.') and os.name != 'nt':
        interfaces = [
            'eth0',
            'eth1',
            'eth2',
            'wlan0',
            'wlan1',
            'wifi0',
            'ath0',
            'ath1',
            'ppp0',
        ]
        for ifname in interfaces:
            try:
                ip = getInterfaceIp(ifname)
                break
            except IOError:
                pass
    return ip

def main():
    print getLocalIpAddress()

if __name__ == '__main__':
    main()
