#!/usr/bin/python3
import time
import bisect
import threading
import random

from peer import peerdict, LocalPeer
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
    def __init__(self, sock):
        super().__init__()
        self.tasks = []
        self.sock = sock

    def load_peer(self, pdx):
        for p in pdx.values():
            test = Test(time.monotonic() + p.period*random.random(), p)
            self.tasks.append(test)
        self.tasks.sort(key=lambda x: x.t)

    def test(self, peer):
        if isinstance(peer, LocalPeer):
            peer.check_update_addr()
        else:
            s = bytearray()
            if peer.pubkey is None:
                s.append(Commd.GK.value)
            s.append(Commd.GA.value)
            self.sock.sendto(bytes(s), peer.addr_tuple)
            print('test', peer.name)

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
            test.peer.last_test_recv = False
            dt = test.t - time.monotonic()
            if dt > 0:
                time.sleep(dt)
                bisect.insort(self.tasks, test.next1())
            else:
                bisect.insort(self.tasks, test.next2())
            self.test(test.peer)
