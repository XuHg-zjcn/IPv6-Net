#!/bin/python3
########################################################################
'''同步通信地址的客户端'''
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
import random
import time
import struct
import socket
import ipaddress
import sqlite3
from enum import Enum

from threading import Thread
from queue import Queue
from python_hosts import Hosts, HostsEntry

from db import HostTable
import ip46
import conf
from peer import peerdict


soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soc.bind(('0.0.0.0', 4646))


class Commd(Enum):  #
    GTN = 0x00      # None
    GTA = 0x01      # None
    POA = 0x03      # idnefer(4B), version(4B), ipv6(16B)


class SyncTask(Thread):
    def __init__(self, p, init_set=None):
        super().__init__()
        self.data = struct.pack('>BII', Commd.POA.value, int(p.ipv4), p.version) + \
                int(p.ipv6).to_bytes(16, 'big')
        self.peer = p
        if init_set is None:
            init_set = set()
        self.knows = init_set  #这些节点已经有数据了

    def run(self):
        while len(self.knows) < len(peerdict.d):
            p4 = random.sample(peerdict.d.keys(), 1)[0]
            if p4 in self.knows:
                continue
            soc.sendto(self.data, (str(p4), 4646))
            self.knows.add(p4)


class Syncer(Thread):
    def __init__(self):
        super().__init__()
        self.hosts = Hosts(path=conf.hosts_file)
        self.queue = Queue()
        self.hlst = []

    def init_pull(self):
        #程序启动后，与已知节点通信，获取更新
        #不触发SyncTask
        pass

    def run(self):
        while True:
            data, addr = soc.recvfrom(1000)
            if data[0] == Commd.GTN.value:
                soc.sendto(conf.client_name.encode(), addr)
            elif data[0] == Commd.GTA.value:
                soc.sendto(ip46.get_local_ipv6(), addr)
            elif data[0] == Commd.POA.value:
                ipv4int, version = struct.unpack('>II', data[1:9])
                p = peerdict.find_v4(ipv4int)
                if version > p.version:
                    ipv6int = int.from_bytes(data[9:25], 'big')
                    ipv6 = ipaddress.IPv6Address(ipv6int)
                    p.ipv6 = ipv6
                    p.version = version
                    p.update_ipv6(ipaddress.IPv6Address(ipv6int), version)
                    SyncTask(p).start()

#TODO: start SyncTask when update local addresss
