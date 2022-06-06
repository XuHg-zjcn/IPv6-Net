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
import time
import random
import struct
import queue
import bisect

from threading import Thread

from peer import peerdict
from protol import Commd


class SyncTask:
    def __init__(self, p, m=3, delay=1, rdelay=0.2, knows=None):
        tmp = bytearray()
        tmp.append(Commd.PK.value)
        tmp.extend(p.pubkey.to_bytes())
        tmp.append(Commd.PA.value)
        tmp.extend(p.ipv6.packed)
        tmp.extend(p.addr_sign)
        self.m = min(m, len(peerdict.dk)-1)  # 计划发送次数
        self.count = 0                       # 已发送次数
        self.data = bytes(tmp)
        self.peer = p
        self.tnext = None
        self.delay = delay
        self.rdelay = rdelay
        if knows:
            self.knows = sorted(map(lambda x:peerdict.lst.index(x), knows))
        else:
            self.knows = []
        self.next2()

    def __lt__(self, other):
        return self.tnext < other.tnext

    def next1(self):
        self.tnext += self.delay + self.rdelay*random.random()

    def next2(self):
        self.tnext = time.monotonic() + self.delay + self.rdelay*random.random()

    def choice_target(self):
        # TODO: peerdict节点变动时更新self.knows
        if len(self.knows) >= len(peerdict.lst):
            return None
        i0 = i1 = random.randrange(len(peerdict.lst) - len(self.knows))
        while True:
            i2 = i0 + bisect.bisect(self.knows, i1)
            if i1 == i2:
                break
            else:
                i1 = i2
        bisect.insort(self.knows, i2)
        p = peerdict.lst[i2]
        return p


class SyncThread(Thread):
    def __init__(self, sock):
        super().__init__()
        self.q = queue.Queue()
        self.tasks = []
        self.sock = sock

    def next_task(self):
        if len(self.tasks) == 0:
            self.tasks.append(self.q.get())
        while True:
            wait = self.tasks[0].tnext - time.monotonic()
            if wait <= 0:
                # 超出时间
                task = self.tasks.pop(0)
                task.next2()
                return task
            try:
                x = self.q.get(timeout=wait)
            except queue.Empty:
                # 时间刚刚好
                task = self.tasks.pop(0)
                task.next1()
                return task
            else:
                bisect.insort(self.tasks, x)

    def run(self):
        while True:
            task = self.next_task()
            target = task.choice_target()
            if target is None:
                continue
            print('sync', target.name)
            self.sock.sendto(task.data, target.addr_tuple)
            task.count += 1
            if task.count < task.m:
                bisect.insort(self.tasks, task)
