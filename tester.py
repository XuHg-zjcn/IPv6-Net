#!/usr/bin/python3
import time
import bisect
import threading
import random

from peer import peerdict
from server import soc
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
    def __init__(self):
        super().__init__()
        self.l = []

    def load_peer(self, pdx):
        for p in pdx.values():
            self.l.append(Test(time.monotonic() + p.period*random.random(), p))
        self.l.sort(key=lambda x:x.t)

    def test(self, peer):
        soc.sendto(bytes([Commd.GTA.value]), peer.addr_tuple)

    def test_all(self):
        for T in self.l:
            self.test(T.peer)

    def run(self):
        self.load_peer(peerdict.d)
        self.test_all()
        while True:
            test = self.l.pop(0)
            dt = test.t - time.monotonic()
            if dt > 0:
                time.sleep(dt)
                bisect.insort(self.l, test.next1())
            else:
                bisect.insort(self.l, test.next2())
            self.test(test.peer)
