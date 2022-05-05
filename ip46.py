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
import netifaces

def get_local_ipv6():
    last = None
    for iface in netifaces.interfaces():
        ifa = netifaces.ifaddresses(iface)
        ipv6 = ifa.get(netifaces.AF_INET6)
        if not ipv6:
            continue
        for i in ipv6[::-1]:
            try:
                last = ipaddress.IPv6Address(i['addr'])
            except ipaddress.AddressValueError:
                pass
            else:
                break
    return last


def ClientUDP(s, ipv4, timeout=10):
    s.sendto(b'\x01', (ipv4, 4646))
    r = s.recv(10000)
    s.close()
    return r

