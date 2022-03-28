#!/usr/bin/python3
########################################################################
'''同步通信地址的服务器'''
# Copyright (C) 2022  Xu Ruijun
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
########################################################################
import ipaddress
import socket
import os

#TODO: add sign
def get_local_ipv6():
    p = os.popen("ifconfig")
    devs = p.read().split('\n\n')
    ret = None
    for dev in devs:
        if not dev:
            break
        lines = dev.split('\n')
        line0 = lines[0].split()
        if "LOOPBACK" in line0[1]:
            continue
        tmp = [line0[0]]
        for line in lines[1:]:
            w = line.split()
            tp, addr = w[:2]
            if tp == 'inet6' and '<global>' in line:
                ret = addr
    if ret is None:
        return b''
    else:
        return int(ipaddress.IPv6Address(ret)).to_bytes(16, 'big')

def ClientUDP(s, ipv4, timeout=10):
    s.sendto(b'\x01', (ipv4, 4646))
    r = s.recv(10000)
    s.close()
    return r

