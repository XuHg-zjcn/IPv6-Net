#!/bin/python3
########################################################################
'''对等节点数据保存'''
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
import struct
import socket
import queue
import threading
import sqlite3

from db import HostTable


q = queue.Queue()

class Peer:
    def __init__(self, name, did, version, ipv4, ipv6=None, period=60.0):
        self.name = name
        self.did = did
        self.version = version
        if ipv6 is not None:
            ipv6 = ipaddress.IPv6Address(ipv6)
        if ipv4 is not None:
            ipv4 = ipaddress.IPv4Address(ipv4)
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.addr_tuple = (str(ipv4), 4646)
        self.period = period

    def __bytes__(self):
        return int(self.ipv6).to_bytes(16, 'big')

    def update_ipv6(self, ipv6, version):
        self.ipv6 = ipv6
        self.version = version
        q.put((self.did, ipv6, version))


class PeerDict(threading.Thread):
    def __init__(self):
        super().__init__()
        self.d = {}

    def add(self, peer):
        self.d[peer.ipv4] = peer

    def load_db(self):
        res = self.htab.get_conds_execute(fields=['name', 'id', 'version', 'ipv4', 'ipv6', 'test_period'])
        for fields in res:
            p = Peer(*fields)
            self.add(p)

    def find_v4(self, v4):
        return self.d[ipaddress.IPv4Address(v4)]

    def run(self):
        conn = sqlite3.connect('data.db')
        self.htab = HostTable(conn)
        self.load_db()
        while True:
            p = q.get()
            self.htab.update_ipv6(*p)


peerdict = PeerDict()
peerdict.start()
