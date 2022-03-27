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
import socket
import os

#TODO: add sign
def get_desc():
    p = os.popen("ifconfig")
    devs = p.read().split('\n\n')
    dv = []
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
            if tp in {'inet', 'ether'} or '<global>' in line:
                tmp.append(f'{tp} {addr}')
        dv.append('\n'.join(tmp))
    return '\n\n'.join(dv)

def ServerUDP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', 4646))
    while True:
        data, addr = s.recvfrom(1000)
        s.sendto(get_desc().encode(), addr)
        print(addr)

def ClientUDP(ipv4, timeout=10):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    s.sendto(b'', (ipv4, 4646))
    r = s.recv(10000)
    s.close()
    return r.decode()


if __name__ == '__main__':
    ServerUDP()
