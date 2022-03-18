#!/bin/python3
import random
import time

from threading import Thread
from queue import Queue
from python_hosts import Hosts, HostsEntry

from db import htab
from ip46 import ClientUDP


class Host(Thread):
    def __init__(self, table, did, queue):
        self.table = table
        self.did = did
        self.hname, self.period, self.ipv4, self.ipv6 = \
            table.get_conds_onlyone({'id':did}, fields=('name', 'test_period', 'ipv4', 'ipv6'))
        self.queue = queue
        Thread.__init__(self)

    def update(self):
        resp = None
        for i in range(10):
            try:
                resp = ClientUDP(self.ipv4)
            except Exception:
                pass
            finally:
                break
        else:
            return
        ipv6 = self.ipv6
        for line in resp.split('\n'):
            words = line.split()
            if len(words) == 2 and words[0] == 'inet6':
                ipv6 = words[1]
        if ipv6 != self.ipv6:
            self.queue.put((self.hname, self.did, ipv6))
            self.ipv6 = ipv6
        else:
            self.queue.put((self.hname, self.did,))

    def run(self):
        self.update()
        time.sleep(self.period * random.random())
        while True:
            self.update()
            time.sleep(self.period)


class Syncer:
    def __init__(self):
        self.hosts = Hosts(path='hosts_test')
        self.queue = Queue()
        self.hlst = []

    def start_all(self):
        for did in htab.get_conds_execute(fields=('id')):
            h = Host(htab, did, self.queue)
            self.hlst.append(h)
            h.start()
        while True:
            ele = self.queue.get()
            if len(ele) == 2:
                htab.inc_time(ele[1])
                hname = ele[0]
                print(f'{hname} : keep')
            else:
                htab.update_ipv6(*ele[1:])
                hname, did, ipv6 = ele
                self.hosts.remove_all_matching('ipv6', hname)
                target = HostsEntry(entry_type='ipv6', address=ipv6, names=[hname])
                self.hosts.add([target])
                self.hosts.write()
                print(f'{hname} : {ipv6}')
