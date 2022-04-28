#!/usr/bin/python3
import time
import bisect
import threading
import socket

from peer import peerdict
from server import soc

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
        for k, v in pdx.items():
            self.l.append(Test(time.monotonic()+v.period, k))
        self.l.sort(key=lambda x:x.t)

    def test(self, peer):
        soc.sendto(bytes([Commd.GTA.value]), peer.addr_tuple)

    def run(self):
        self.load_peer(peerdict.d)
        while True:
            test = self.l.pop(0)
            dt = test.t - time.monotonic()
            if dt > 0:
                time.sleep(dt)
                bisect.insort(self.l, test.next1())
            else:
                bisect.insort(self.l, test.next2())
            self.test(test.peer)
