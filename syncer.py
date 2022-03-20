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
import random
import time

from threading import Thread
from queue import Queue
from python_hosts import Hosts, HostsEntry

from db import htab
from ip46 import ClientUDP
import conf


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
        for i in range(2):
            try:
                resp = ClientUDP(self.ipv4)
            except Exception:
                pass
            else:
                break
        else:
            self.queue.put((self.hname, self.did, False))
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
            self.queue.put((self.hname, self.did, True))

    def run(self):
        self.update()
        time.sleep(self.period * random.random())
        while True:
            self.update()
            time.sleep(self.period)


class Syncer:
    def __init__(self):
        self.hosts = Hosts(path=conf.hosts_file)
        self.queue = Queue()
        self.hlst = []

    def start_all(self):
        for did in htab.get_conds_execute(fields=('id')):
            h = Host(htab, did, self.queue)
            self.hlst.append(h)
            h.start()
        while True:
            hname, did, state = self.queue.get()
            if state == False:
                print(f'{hname} : faild')
                htab.disconn(did)
            elif state == True:
                htab.inc_time(did)
                print(f'{hname} : keep')
            else:
                hname += conf.domain_suffix
                ipv6 = state
                htab.update_ipv6(did, ipv6)
                self.hosts.remove_all_matching('ipv6', hname)
                target = HostsEntry(entry_type='ipv6', address=ipv6, names=[hname])
                self.hosts.add([target])
                self.hosts.write()
                print(f'{hname} : {ipv6}')
