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
import logging

import conf
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
    def __init__(self, sock4, sock6, syncth):
        super().__init__()
        self.tasks = []
        self.sock4 = sock4
        self.sock6 = sock6
        self.syncth = syncth

    def load_peer(self, pdx):
        for p in pdx:
            test = Test(time.monotonic() + p.period*random.random(), p)
            self.tasks.append(test)
        self.tasks.sort(key=lambda x: x.t)

    def test(self, peer):
        if isinstance(peer, LocalPeer):
            if peer.check_update_addr():
                try:
                    stask = SyncTask(peer, m=10, knows=[peer])
                except Exception as e:
                    logging.exception(f'start SyncTask faild, {e}')
                else:
                    self.syncth.q.put(stask)
        else:
            s = bytearray()
            if conf.test_require_time:
                s.append(Commd.GT.value)
            if peer.pubkey is None:
                s.append(Commd.GK.value)
            s.append(Commd.PV.value)
            s.extend(peerdict.local.version.to_bytes(8, 'big'))
            s.append(Commd.InVg.value)
            s.extend(peer.version.to_bytes(8, 'big'))
            s.append(Commd.GA.value)
            if conf.test_report_time:
                s.append(Commd.PT.value)
                s.extend(int(time.time()*2**24).to_bytes(8, 'big'))
            if conf.test_require_sign:
                s.append(Commd.GS.value)
            if conf.test_report_sign:
                s.append(Commd.PS.value)
                s.extend(conf.sk.sign(bytes(s)))
            s = bytes(s)
            if peer.last_addr == 4:
                self.sock4.sendto(s, (peer.ipv4.compressed, 4646))
                logging.info(f'test {peer.name} ({peer.ipv4.compressed})')
            elif peer.last_addr == 6:
                self.sock6.sendto(s, (peer.ipv6.compressed, 4646))
                logging.info(f'test {peer.name} ({peer.ipv6.compressed})')
            else:
                logging.warning(f'peer.last_addr = {peer.last_addr}')

    def test_all(self):
        for T in self.tasks:
            self.test(T.peer)

    def run(self):
        time.sleep(1)  # 等待数据库加载完成
        self.load_peer(peerdict.lst)
        self.test_all()
        while True:
            test = self.tasks.pop(0)
            if not isinstance(test.peer, LocalPeer) and \
               not test.peer.last_test_recv:
                test.peer.disconn()
                if test.peer.last_addr == 4 and test.peer.ipv6:
                    test.peer.last_addr = 6
                elif test.peer.last_addr == 6 and test.peer.ipv4:
                    test.peer.last_addr = 4
            test.peer.last_test_recv = False
            dt = test.t - time.monotonic()
            if dt > 0:
                time.sleep(dt)
                bisect.insort(self.tasks, test.next1())
            else:
                bisect.insort(self.tasks, test.next2())
            self.test(test.peer)
