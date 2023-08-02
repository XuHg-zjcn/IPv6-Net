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
import time
import struct
import threading
import logging
import ed25519

import conf
from peer import peerdict, q
from protol import Commd


class Procer:
    def __init__(self, data, pp, addr):
        self.data = data
        self.addr = addr
        self.i = 0
        self.res = bytearray()
        # 没有使用TG指令指定目标时，设置默认操作主机
        self.pg = peerdict.local        # Gx指令操作的主机，默认本机
        self.pp = pp                    # Px指令操作的主机，默认对方
        self.pp0 = pp                   # 发送节点

    def GN(self):
        self.i += 1
        if not self.pg:
            return
        self.res.append(Commd.PN.value)
        self.res.extend(struct.pack('>H', len(self.pg.name)))
        self.res.extend(self.pg.name.encode())

    def PN(self):
        self.i += 1
        self.i += int.from_bytes(self.data[self.i:self.i+2], 'big')
        self.i += 66

    def GA(self):
        self.i += 1
        if not self.pg:
            return
        if self.pg == peerdict.local:
            self.pg.check_update_addr()
        self.res.append(Commd.PA.value)
        self.res.extend(struct.pack('>Q', self.pg.version))
        # TODO: 处理无法获取IPv6地址情况
        self.res.extend(self.pg.ipv6.packed)
        if self.pg.addr_sign:
            self.res.extend(self.pg.addr_sign)
        else:
            self.res.extend(bytes(64))

    def PA(self):
        if self.pp and self.pp != peerdict.local:
            ver_old = self.pp.version
            verify, ver, ipv6 = self.pp.put_addr(self.data[self.i:self.i+89])
            if self.pp0 is None and verify and ver >= ver_old and ipv6 == self.addr[0]:
                self.pp0 = self.pp  # 发送节点已确定
        self.i += 89

    def GK(self):
        self.i += 1
        if not self.pg:
            return
        self.res.append(Commd.PK.value)
        self.res.extend(self.pg.pubkey.to_bytes())

    def PK(self):
        self.i += 1
        x = self.data[self.i:self.i+32]
        p = peerdict.dk.get(x)
        self.i += 32
        if p is None:
            if self.pp and self.pp.pubkey is None:
                q.put(('update_conds', {'id':self.pp.did}, {'pubkey':x}))
                self.pp.pubkey = ed25519.VerifyingKey(x)
                strkey = self.pp.pubkey.to_ascii(encoding='base64')
                logging.info(f'get {self.pp.name} pubkey {strkey}')
            else:
                self.res.append(Commd.NF.value)
        else:
            p.last_test_recv = True
        self.pg = self.pp = p

    def GI(self):
        self.i += 1
        if not self.pg:
            return
        self.res.append(Commd.PI.value)
        # TODO: 添加支持
        self.res.extend(struct.pack('>QH'), 0, 0)
        self.res.extend(bytes(64))

    def GV(self):
        if not self.pg:
            return
        self.res.append(self.pg.version.to_bytes(8, 'big'))

    def PV(self):
        self.i += 1
        ver = int.from_bytes(self.data[self.i:self.i+8], 'big')
        if self.pp and ver > self.pp.version:
            self.res.append(Commd.GA.value)
        self.i += 8

    def InVg(self):
        self.i += 1
        ver_ = int.from_bytes(self.data[self.i:self.i+8], 'big')
        if ver_ >= self.pg.version:
            self.pg = None
        self.i += 8

    def GT(self):
        self.i += 1
        if self.pg == peerdict.local:
            t = time.time()
            self.res.append(Commd.PT.value)
            self.res.extend(int(t*2**24).to_bytes(8, 'big'))

    def PT(self):
        self.i += 1
        if self.pp and self.pp != peerdict.local:
            ts = int.from_bytes(self.data[self.i:self.i+8], 'big')/2**24
            if abs(ts - time.time()) < conf.time_update_tolerate:
                self.pp.last_test_recv = True
                self.pp.inc_time(ts)
        self.i += 8

    def proc(self):
        while self.i < len(self.data):
            # 获取命令名
            try:
                fname = Commd(self.data[self.i]).name
            except ValueError:
                logging.error(f'unkown commd 0x{self.data[self.i]:02x}')
                break
            # 根据命令名找到方法的函数
            try:
                func = getattr(self, fname)
            except AttributeError:
                logging.error(f'not implemented commd {fname}')
                break
            # 执行函数
            try:
                func()
            except Exception as e:
                logging.exception(f'exception during exec {fname}: {e}')
                break
            # 有一个环节出错就记录日志并跳出循环，保留之前的数据
        if not self.pp0 and self.data[0] != Commd.PK.value:
            # 还不知道对方节点，请求公钥和带签名的地址
            self.res.insert(0, Commd.GK.value)
            self.res.insert(1, Commd.GA.value)
        if self.pp0 and self.pp0.pubkey is None:
            # 知道对方节点，但不知道对方公钥，请求公钥
            self.res.insert(0, Commd.GK.value)
        return bytes(self.res)


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
            # TODO: 处理找不到默认pp的情况
            pp = self.find_p(addr[0])
            if pp is None:
                pp_name = 'Unknown'
            else:
                pp.last_test_recv = True
                pp_name = pp.name
            logging.debug(f'from {pp_name} {addr[:2]}')
            logging.debug(f'recv {data.hex()}')

            res = Procer(data, pp, addr).proc()

            if len(res) > 0:
                self.sock.sendto(res, addr[:2])
            logging.debug(f'resp {res.hex()}')
