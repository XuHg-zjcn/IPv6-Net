#!/bin/python3
########################################################################
'''UDP服务器'''
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
import socket
import struct
import threading
import ipaddress
from queue import Queue

import ip46
import conf
from peer import peerdict
from protol import Commd


soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soc.bind(('0.0.0.0', 4646))

class Server(threading.Thread):
    def __init__(self):
        super().__init__()
        self.queue = Queue()
        self.hlst = []

    def run(self):
        while True:
            data, addr = soc.recvfrom(1000)
            if data[0] == Commd.GTN.value:
                pack = bytes([Commd.PTN.value])
                pack = pack + conf.client_name.encode()
                soc.sendto(pack, addr)
                print('GTN')
            elif data[0] == Commd.GTA.value:
                # TODO: 从数据库中读取IPv6和版本，判断IPv6是否变化，变化则更新版本
                version = 1
                pack = struct.pack('>BI', Commd.PTA.value, version)
                pack = pack + ip46.get_local_ipv6()
                soc.sendto(pack, addr)
                print('GTA')
            elif data[0] == Commd.PTA.value:
                ipv4str = addr[0]
                version = int.from_bytes(data[1:5], 'big')
                ipv6int = int.from_bytes(data[5:21], 'big')
                p = peerdict.find_v4(ipv4str)
                p.update_ipv6(ipaddress.IPv6Address(ipv6int), version)
                print('PTA', ipv4str)
            elif data[0] == Commd.POA.value:
                ipv4int, version = struct.unpack('>II', data[1:9])
                p = peerdict.find_v4(ipv4int)
                if version > p.version:
                    ipv6int = int.from_bytes(data[9:25], 'big')
                    p.update_ipv6(ipaddress.IPv6Address(ipv6int), version)
                    #SyncTask(p).start()
                print('POA')
