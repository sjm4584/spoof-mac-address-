#!/usr/bin/env python

import sys
import fcntl
import array
import struct
import socket
import platform
import argparse
import sys
import os
import random
import subprocess
from uuid import getnode as get_mac

# global constants.  If you don't like 'em here,
# move 'em inside the function definition.
SIOCGIFCONF = 0x8912
MAXBYTES = 8096


# gets all current interfaces. Not really needed but neat code
def localifs():
    """
    Used to get a list of the up interfaces and associated IP addresses
    on this machine (linux only).

    Returns:
        List of interface tuples.  Each tuple consists of
        (interface name, interface IP)
    """
    global SIOCGIFCONF
    global MAXBYTES

    arch = platform.architecture()[0]

    # I really don't know what to call these right now
    var1 = -1
    var2 = -1
    if arch == '32bit':
        var1 = 32
        var2 = 32
    elif arch == '64bit':
        var1 = 16
        var2 = 40
    else:
        raise OSError("Unknown architecture: %s" % arch)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B', '\0' * MAXBYTES)
    outbytes = struct.unpack('iL', fcntl.ioctl(
        sock.fileno(),
        SIOCGIFCONF,
        struct.pack('iL', MAXBYTES, names.buffer_info()[0])
        ))[0]

    namestr = names.tostring()
    return [(namestr[i:i+var1].split('\0', 1)[0],
            socket.inet_ntoa(namestr[i+20:i+24]))
            for i in xrange(0, outbytes, var2)]


# get MAC address of a given interface in octet form
def get_mac(interface):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', interface[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]


# generates and changes the MAC address using ip command
def change_mac(interface, mac):
    mac = mac[:9]
    seed = "abcdef0123456789"
    mac += ':'.join(
        [random.choice(seed) + random.choice(seed) for _ in range(3)])
    process = subprocess.Popen('ip link set %s down' % (interface),
                               shell=True, stdout=subprocess.PIPE)
    process = subprocess.Popen('ip link set %s address %s' % (interface,
                               mac), shell=True, stdout=subprocess.PIPE)
    process = subprocess.Popen('ip link set %s up' % (interface),
                               shell=True, stdout=subprocess.PIPE)
    process.wait()
    print "[+] New MAC Address is: ", mac

    return process.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-int', '--interface', type=str, help='interface to change')
    parser.add_argument(
        '-ls', '--list', help='list available interfaces',
        action='store_true')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        exit()

    if args.list:
        interfaces = localifs()
        mac = {}
        for i in range(0, len(interfaces)):
            print interfaces[i][0], ":", get_mac(interfaces[i][0]), ":", \
                interfaces[i][1]
        exit()

    mac = get_mac(args.interface)
    print "[+] Old MAC Address is: ", mac
    status = change_mac(args.interface, mac)
    print "status: ", status

if __name__ == '__main__':
    sys.exit(main())
