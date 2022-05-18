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
import struct
import threading

from peer import peerdict
from protol import Commd


class Server(threading.Thread):
    def __init__(self, sock, find_p):
        '''
        :sock: UDP socket
        :find_p: func addr->peer
        '''
        super().__init__()
        self.hlst = []
        self.sock = sock
        self.find_p = find_p

    def run(self):
        while True:
            data, addr = self.sock.recvfrom(1000)
            i = 0
            res = bytearray()
            # 没有使用TG指令指定目标时，设置默认操作主机
            pg = peerdict.local        # Gx指令操作的主机，默认本机
            pp = self.find_p(addr[0])  # Px指令操作的主机，默认对方
            # TODO: 处理找不到默认pp的情况
            while i < len(data):
                if data[i] == Commd.TG.value:
                    i += 1
                    p = peerdict.dk.get(data[i:i+32])
                    i += 32
                    if p is None:
                        res.append(Commd.NF.value)
                        break
                    pg = pp = p
                elif data[i] == Commd.GN.value:
                    i += 1
                    res.append(Commd.PN.value)
                    res.extend(struct.pack('>H', len(pg.name)))
                    res.extend(pg.name.encode())
                elif data[i] == Commd.PN.value:
                    i += 1
                    i += int.from_bytes(data[i:i+2], 'big')
                    i += 66
                elif data[i] == Commd.GA.value:
                    i += 1
                    res.append(Commd.PA.value)
                    res.extend(struct.pack('>Q', pg.version))
                    # TODO: 处理无法获取IPv6地址情况
                    if pg == peerdict.local:
                        pg.check_update_addr()
                    res.extend(pg.ipv6.packed)
                    if pg.addr_sign:
                        res.extend(pg.addr_sign)
                    else:
                        res.extend(bytes(64))
                elif data[i] == Commd.PA.value:
                    if pp != peerdict.local:
                        pp.put_addr(data[i:i+89])
                    i += 89
                elif data[i] == Commd.GK.value:
                    i += 1
                    res.append(Commd.PK.value)
                    res.extend(pg.pubkey)
                elif data[i] == Commd.PK.value:
                    if pp != peerdict.local:
                        pp.put_pubkey(data[i:i+33])
                    i += 33
                elif data[i] == Commd.GI.value:
                    i += 1
                    res.append(Commd.PI.value)
                    # TODO: 添加支持
                    res.extend(struct.pack('>QH'), 0, 0)
                    res.extend(bytes(64))
                else:
                    i += 1
            if len(res) > 0:
                self.sock.sendto(bytes(res), addr)
