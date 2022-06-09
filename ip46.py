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
import os
import time
import socket
import logging
import threading
import ipaddress
import netifaces


LANNets = [
    ipaddress.IPv4Network('10.0.0.0/8'),
    ipaddress.IPv4Network('172.16.0.0/12'),
    ipaddress.IPv4Network('192.168.0.0/16'),
    ]


def get_local_addr():
    def find_addr(w, spt):
        x = list(filter(lambda x: w in x, spt))
        if len(x) > 0:
            x = x[0].split()[1].split('/')[0]
        else:
            x = None
        return x
    with os.popen('ip address show scope global primary') as p:
        res = p.read()
    spt = res.split('\n')
    x4 = find_addr('inet', spt)
    x6 = find_addr('inet6', spt)
    if x4:
        x4 = ipaddress.IPv4Address(x4)
    if x6:
        x6 = ipaddress.IPv6Address(x6)
    return x4, x6


def a2s_4(addr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((addr.compressed, 4646))
    sock.settimeout(1)  # recvfrom时，在另一个线程中close后，仍然会阻塞
    return sock         # 设置一个超时时间，每次调用recvfrom最多阻塞1s


def a2s_6(addr):
    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    sock.bind((addr.compressed, 4646))
    sock.settimeout(1)
    return sock


class IPState:
    def __init__(self, a2s):
        self.addr = None
        self.sock = None
        self.a2s = a2s
        self.event = threading.Event()

    def clear(self):
        self.event.clear()
        self.addr = None
        if self.sock:
            self.sock.close()
        self.sock = None

    def update(self, addr):
        if addr != self.addr:
            old_addr = self.addr
            self.clear()
            if addr is not None:
                # 延时改为1会出现OSError: [Errno 99] Cannot assign requested address
                time.sleep(2)
                self.addr = addr
                self.sock = self.a2s(addr)
                self.event.set()
            logging.info(f'addr change {old_addr} -> {addr}')

    def sendto(self, data, addr):
        while True:
            self.event.wait()
            try:
                r = self.sock.sendto(data, addr)
            except (OSError, AttributeError) as e:
                time.sleep(1)
            else:
                return r

    def recvfrom(self, size):
        while True:
            self.event.wait()
            try:
                r = self.sock.recvfrom(size)
            except (OSError, AttributeError) as e:
                time.sleep(1)
            else:
                return r


# TODO: 使用`ip monitor address`监测地址变化
class IPMon(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stat4 = IPState(a2s_4)
        self.stat6 = IPState(a2s_6)

    def run(self):
        while True:
            addr4, addr6 = get_local_addr()
            self.stat4.update(addr4)
            self.stat6.update(addr6)
            time.sleep(1)
