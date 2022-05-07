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

import ip46
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
        self.last_test_recv = False

    def update_ipv6(self, ipv6, version, sign):
        self.ipv6 = ipv6
        self.version = version
        self.addr_sign = sign
        hname = self.name + conf.domain_suffix
        hosts.remove_all_matching('ipv6', hname)
        target = HostsEntry(entry_type='ipv6', address=str(ipv6), names=[hname])
        hosts.add([target])
        hosts.write()
        q.put(('update_ipv6', self.did, ipv6, version, sign))

    def inc_time(self):
        self.last_test_recv = True
        q.put(('inc_time', self.did))

    def disconn(self):
        q.put(('disconn', self.did))

    def put_addr(self, data):
        assert data[0] == Commd.PA.value
        ver = int.from_bytes(data[1:9], 'big')
        ipv6 = ipaddress.IPv6Address(data[9:25])
        sign = data[25:89]
        try:
            self.pubkey.verify(sign, data[:25])
        except ed25519.BadSignatureError:
            print('sign error', self.name)
            return None
        else:
            self.inc_time()
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


class LocalPeer(Peer):
    def check_update_addr(self):
        ipv4, ipv6 = ip46.get_local_addr()
        if ipv6 != self.ipv6:
            ver = self.version + 1
            tmp = bytearray()
            tmp.append(Commd.PA.value)
            tmp.extend(ver.to_bytes(8, 'big'))
            tmp.extend(ipv6.packed)
            sign = conf.sk.sign(bytes(tmp))
            self.update_ipv6(ipv6, ver, sign)
        self.inc_time()
        #TODO: 起动SyncTask

    def put_addr(self, data):
        # 禁止用数据更新本机地址
        pass

    def put_pubkey(self, data):
        # 禁止用数据更新本机公钥
        pass


class PeerDict(threading.Thread):
    def __init__(self):
        super().__init__()
        self.dk = {}
        self.d6 = {}
        self.d4 = {}
        self.local = None

    def add(self, peer):
        self.dk[peer.pubkey.to_bytes()] = peer
        self.d6[peer.ipv6] = peer
        self.d4[peer.ipv4] = peer

    def load_db(self):
        res = self.htab.get_conds_execute(fields=['name', 'pubkey', 'id', 'version', 'ipv4', 'ipv6', 'addr_sign', 'test_period'])
        for fields in res:
            if fields[2] == 0:
                p = LocalPeer(*fields)
                self.local = p
            else:
                p = Peer(*fields)
            self.add(p)

    def run(self):
        #sqlite只支持单线程操作,所以把所有sqlite操作都放到这里
        conn = sqlite3.connect(conf.db_path)
        self.htab = HostTable(conn)
        self.load_db()
        while True:
            p = q.get()
            getattr(self.htab, p[0])(*p[1:])


peerdict = PeerDict()
peerdict.start()
