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
import netifaces


LANNets = [
    ipaddress.IPv4Network('10.0.0.0/8'),
    ipaddress.IPv4Network('172.16.0.0/12'),
    ipaddress.IPv4Network('192.168.0.0/16'),
    ]


def get_local_addr():
    last4 = None
    last6 = None
    for iface in netifaces.interfaces():
        ifa = netifaces.ifaddresses(iface)
        ipv4 = ifa.get(netifaces.AF_INET)
        ipv6 = ifa.get(netifaces.AF_INET6)
        if ipv4 and not last4:
            for i in ipv4:
                addr = ipaddress.IPv4Address(i['addr'])
                if any(addr in net for net in LANNets):
                    last4 = addr
                    break
        if ipv6 and not last6:
            for i in ipv6:
                addr = i['addr']
                if '%' in addr:
                    continue
                tmp = ipaddress.IPv6Address(addr)
                if tmp.is_global:
                    last6 = tmp
                    break
    return last4, last6


def ClientUDP(s, ipv4, timeout=10):
    s.sendto(b'\x01', (ipv4, 4646))
    r = s.recv(10000)
    s.close()
    return r
