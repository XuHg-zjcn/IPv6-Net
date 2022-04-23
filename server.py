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
import threading
import ipaddress

from queue import Queue
from python_hosts import Hosts, HostsEntry

import ip46
import conf
from peer import peerdict
from protol import Commd


soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soc.bind(('0.0.0.0', 4646))

class Server(threading.Thread):
    def __init__(self):
        super().__init__()
        self.hosts = Hosts(path=conf.hosts_file)
        self.queue = Queue()
        self.hlst = []

    def run(self):
        while True:
            data, addr = soc.recvfrom(1000)
            if data[0] == Commd.GTN.value:
                soc.sendto(conf.client_name.encode(), addr)
            elif data[0] == Commd.GTA.value:
                soc.sendto(ip46.get_local_ipv6(), addr)
            elif data[0] == Commd.POA.value:
                ipv4int, version = struct.unpack('>II', data[1:9])
                p = peerdict.find_v4(ipv4int)
                if version > p.version:
                    ipv6int = int.from_bytes(data[9:25], 'big')
                    ipv6 = ipaddress.IPv6Address(ipv6int)
                    p.ipv6 = ipv6
                    p.version = version
                    p.update_ipv6(ipaddress.IPv6Address(ipv6int), version)
                    #SyncTask(p).start()
