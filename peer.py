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
import queue
import threading
import sqlite3
import ed25519
import bisect
import logging

import ip46
import conf
from hosts import Hosts
from db import HostTable, ExchangeTable
from protol import Commd


hosts = Hosts(path=conf.hosts_file, block_name=conf.hosts_block_name)
q = queue.Queue()


class Peer:
    sock4 = None
    sock6 = None
    syncth = None
    def __init__(self, name, pubkey, did,
                 version, ipv4, ipv6=None, addr_sign=None, period=60.0):
        self.name = name
        try:
            self.pubkey = ed25519.VerifyingKey(pubkey)
        except Exception:
            self.pubkey = None
        self.did = did
        self.version = version
        try:
            self.ipv6 = ipaddress.IPv6Address(ipv6)
        except Exception:
            self.ipv6 = None
        try:
            self.ipv4 = ipaddress.IPv4Address(ipv4)
        except Exception:
            self.ipv4 = None
        self.addr_sign = addr_sign or bytes(64)
        self.period = period
        if ipv6:
            last_addr = 6
        elif ipv4:
            last_addr = 4
        else:
            last_addr = None
        self.last_addr = last_addr
        self.last_test_recv = False

    def update_hosts(self, addnew=False):
        hname = self.name + conf.domain_suffix
        hosts.auto_write(hname, str(self.ipv6), addnew)
        hosts.flush()

    def update_ipv6(self, ipv6, version, sign):
        if self.ipv6 and self.ipv6 in peerdict.d6:
            peerdict.d6.pop(self.ipv6)
        self.ipv6 = ipv6
        self.version = version
        self.addr_sign = sign
        peerdict.d6[ipv6] = self
        self.update_hosts()
        q.put((peerdict.htab.update_ipv6, None, self.did, ipv6, version, sign))

    def __getattr__(self, name):
        assert hasattr(HostTable, name) , f"'HostTable' has no attribute '{name}', disallow put to queue"
        assert callable(getattr(HostTable, name)), f"'HostTable.{name}' not callable, disallow put to queue"
        return lambda *args: q.put((getattr(peerdict.htab, name), None, self.did)+args)

    def put_addr(self, data):
        assert len(data) == 89
        assert data[0] == Commd.PA.value
        ver = int.from_bytes(data[1:9], 'big')
        ipv6 = ipaddress.IPv6Address(data[9:25])
        sign = data[25:89]
        if self.pubkey:
            try:
                self.pubkey.verify(sign, data[:25])
            except ed25519.BadSignatureError:
                logging.warning(f'sign error {self.name}')
                verify = False
            else:
                verify = True
                self.inc_time()
                if ver > self.version:
                    logging.info(f'Update IPv6 {self.name} {ipv6} ver{self.version}->{ver}')
                    self.update_ipv6(ipv6, ver, sign)
                    self.updated()
                else:
                    logging.warning(f'Refuse update IPv6 {self.name} {ipv6} ver{self.version}->{ver}')
        else:
            verify = None
        return verify, ver, ipv6

    def put_pubkey(self, data):
        assert len(data) == 33
        assert data[0] == Commd.PK.value
        self.pubkey = ed25519.VerifyingKey(data[1:])
        # TODO: 待实现

    def __lt__(self, other):
        if self.pubkey and other.pubkey:
            return self.pubkey.vk_s < other.pubkey.vk_s
        elif self.name and other.name:
            return self.name < other.name
        elif self.ipv4 and other.ipv4:
            return self.ipv4 < other.ipv4
        else:
            raise ValueError("can't compare")

    def sendto_(self, data):
        if self.last_addr == 4:
            Peer.sock4.sendto(data, (self.ipv4.compressed, 4646))
        elif self.last_addr == 6:
            Peer.sock6.sendto(data, (self.ipv6.compressed, 4646))

    def be_online(self):
        pass

    def be_offline(self):
        pass

    def updated(self):
        q.put((peerdict.etab.set_update,
               lambda x:Peer.syncth.create_task(self, m=5, musts=x),
               self.did))


class LocalPeer(Peer):
    def check_update_addr(self):
        ipv4, ipv6 = ip46.get_local_addr()
        self.inc_time()
        if ipv6 and ipv6 != self.ipv6:
            ver = self.version + 1
            tmp = bytearray()
            tmp.append(Commd.PA.value)
            tmp.extend(ver.to_bytes(8, 'big'))
            tmp.extend(ipv6.packed)
            sign = conf.sk.sign(bytes(tmp))
            self.update_ipv6(ipv6, ver, sign)
            return True
        else:
            return False

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
        self.lst = []
        self.did = {}
        self.local = None

    def find_v4(self, addr):
        return self.d4.get(ipaddress.IPv4Address(addr))

    def find_v6(self, addr):
        return self.d6.get(ipaddress.IPv6Address(addr))

    def find_v46(self, addr):
        addr = ipaddress.IPv6Address(addr)
        if addr.ipv4_mapped:
            return self.find_v4(addr.ipv4_mapped)
        else:
            return self.find_v6(addr)

    def add(self, peer):
        if peer.pubkey:
            self.dk[peer.pubkey.to_bytes()] = peer
        if peer.ipv6:
            self.d6[peer.ipv6] = peer
        if peer.ipv4:
            self.d4[peer.ipv4] = peer
        bisect.insort(self.lst, peer)
        self.did[peer.did] = peer

    def load_db(self):
        res = self.htab.get_conds_execute(
            fields=['name', 'pubkey', 'id',
                    'version', 'ipv4', 'ipv6', 'addr_sign', 'test_period'])
        for fields in res:
            if fields[2] == 0:
                p = LocalPeer(*fields)
                self.local = p
            else:
                p = Peer(*fields)
            self.add(p)
            hname = p.name + conf.domain_suffix
            if hname in hosts.d and p.ipv6:
                try:
                    x = ipaddress.IPv6Address(hosts.d[hname])
                except Exception:
                    p.update_hosts()
                else:
                    if x != p.ipv6:
                        p.update_hosts()

    def run(self):
        # sqlite只支持单线程操作,所以把所有sqlite操作都放到这里
        conn = sqlite3.connect(conf.db_path)
        self.htab = HostTable(conn)
        self.etab = ExchangeTable(conn)
        self.load_db()
        # TODO: 加载完成后同步hosts
        while True:
            p = q.get()
            res = p[0](*p[2:])
            if callable(p[1]):
                p[1](res)


peerdict = PeerDict()
peerdict.start()
