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
import struct

from threading import Thread

from peer import peerdict
from server import soc
from protol import Commd


class SyncTask(Thread):
    def __init__(self, p, init_set=None):
        super().__init__()
        self.data = struct.pack('>BII', Commd.POA.value, int(p.ipv4), p.version) + \
                int(p.ipv6).to_bytes(16, 'big')
        self.peer = p
        if init_set is None:
            init_set = set()
        self.knows = init_set  #这些节点已经有数据了

    def run(self):
        while len(self.knows) < len(peerdict.d4):
            p4 = random.sample(peerdict.d4.keys(), 1)[0]
            if p4 in self.knows:
                continue
            soc.sendto(self.data, (str(p4), 4646))
            self.knows.add(p4)

#TODO: start SyncTask when update local addresss
