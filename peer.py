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
import ed25519

from python_hosts import Hosts, HostsEntry

import conf
from db import HostTable
from protol import Commd


hosts = Hosts(path=conf.hosts_file)
q = queue.Queue()

class Peer:
    def __init__(self, name, pubkey, did, version, ipv4, ipv6=None, addr_sign=None, period=60.0):
        self.name = name
        if pubkey is not None:
            pubkey = ed25519.VerifyingKey(pubkey)
        self.pubkey = pubkey
        self.did = did
        self.version = version
        if ipv6 is not None:
            ipv6 = ipaddress.IPv6Address(ipv6)
        if ipv4 is not None:
            ipv4 = ipaddress.IPv4Address(ipv4)
        self.ipv4 = ipv4
        self.ipv6 = ipv6
        self.addr_sign = addr_sign or bytes(64)
        self.addr_tuple = (str(ipv4), 4646)
        self.period = period

    def __bytes__(self):
        return int(self.ipv6).to_bytes(16, 'big')

    def update_ipv6(self, ipv6, version, sign):
        self.ipv6 = ipv6
        self.version = version
        hname = self.name + conf.domain_suffix
        hosts.remove_all_matching('ipv6', hname)
        target = HostsEntry(entry_type='ipv6', address=str(ipv6), names=[hname])
        hosts.add([target])
        hosts.write()
        q.put((self.did, ipv6, version, sign))

    def put_addr(self, data):
        assert data[0] == Commd.PA.value
        ver = int.from_bytes(data[1:9], 'big')
        ipv6 = int.from_bytes(data[9:25], 'big')
        ipv6 = ipaddress.IPv6Address(ipv6)
        sign = data[25:89]
        try:
            self.pubkey.verify(sign, data[:25])
        except ed25519.BadSignatureError:
            print('sign error', self.name)
            return None
        else:
            if ver > self.version:
                self.update_ipv6(ipv6, ver, sign)
                return True
            else:
                return False

    def put_pubkey(self, data):
        assert len(data) == 33
        assert data[0] == Commd.PK.value
        #self.pubkey = ed25519.VerifyingKey(data[1:])
        #TODO: 待实现


class PeerDict(threading.Thread):
    def __init__(self):
        super().__init__()
        self.dk = {}
        self.d6 = {}
        self.d4 = {}

    def add(self, peer):
        self.dk[peer.pubkey.to_bytes()] = peer
        self.d6[peer.ipv6] = peer
        self.d4[peer.ipv4] = peer

    def load_db(self):
        res = self.htab.get_conds_execute(fields=['name', 'pubkey', 'id', 'version', 'ipv4', 'ipv6', 'addr_sign', 'test_period'])
        for fields in res:
            p = Peer(*fields)
            self.add(p)

    def run(self):
        #sqlite只支持单线程操作,所以把所有sqlite操作都放到这里
        conn = sqlite3.connect(conf.db_path)
        self.htab = HostTable(conn)
        self.load_db()
        while True:
            p = q.get()
            self.htab.update_ipv6(*p)


peerdict = PeerDict()
peerdict.start()
