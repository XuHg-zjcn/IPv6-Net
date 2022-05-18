#!/usr/bin/python3
########################################################################
'''测试目标主机'''
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
import time
import bisect
import threading
import random

from peer import peerdict, LocalPeer
from syncer import SyncTask
from protol import Commd


class Test:
    def __init__(self, t, peer):
        self.t = t
        self.peer = peer

    def __lt__(self, other):
        return self.t < other.t

    def next1(self):
        return Test(self.t + self.peer.period, self.peer)

    def next2(self):
        return Test(time.monotonic() + self.peer.period, self.peer)


class Tester(threading.Thread):
    def __init__(self, sock, syncth):
        super().__init__()
        self.tasks = []
        self.sock = sock
        self.syncth = syncth

    def load_peer(self, pdx):
        for p in pdx.values():
            test = Test(time.monotonic() + p.period*random.random(), p)
            self.tasks.append(test)
        self.tasks.sort(key=lambda x: x.t)

    def test(self, peer):
        if isinstance(peer, LocalPeer):
            if peer.check_update_addr():
                stask = SyncTask(peer, m=10, knows=[peer])
                self.syncth.q.put(stask)
        else:
            s = bytearray()
            if peer.pubkey is None:
                s.append(Commd.GK.value)
            s.append(Commd.GA.value)
            self.sock.sendto(bytes(s), peer.addr_tuple)
            print('test', peer.name, peer.addr_tuple)

    def test_all(self):
        for T in self.tasks:
            self.test(T.peer)

    def run(self):
        time.sleep(1)  # 等待数据库加载完成
        self.load_peer(peerdict.dk)
        self.test_all()
        while True:
            test = self.tasks.pop(0)
            if not test.peer.last_test_recv:
                test.peer.disconn()
                test.peer.addr_tuple = (test.peer.ipv6.compressed, 4646) \
                    if test.peer.addr_tuple[0][:7] == '::ffff:' and test.peer.ipv6 \
                    else ('::ffff:'+test.peer.ipv4.compressed, 4646)
            test.peer.last_test_recv = False
            dt = test.t - time.monotonic()
            if dt > 0:
                time.sleep(dt)
                bisect.insort(self.tasks, test.next1())
            else:
                bisect.insort(self.tasks, test.next2())
            self.test(test.peer)
