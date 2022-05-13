#!/usr/bin/python3
########################################################################
'''Hosts操作'''
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
import ipaddress
from collections import namedtuple


HostsItem = namedtuple('HostsItem', ['pos', 'addr'])


def is_ipv6(addr):
    try:
        ipaddress.IPv6Address(addr)
    except ipaddress.AddressValueError:
        return False
    else:
        return True


class Hosts:
    def __init__(self, path, block_name):
        self.path = path
        self.f = open(path, 'rb+')
        self.block_name = block_name
        self.d = {}
        self.a = None  # start标签的第一个字符
        self.b = None  # end标签后下一行的第一个字符
        self._start_label = f'# {self.block_name} Start\n'.encode()
        self._end_label = f'# {self.block_name} End\n'.encode()
        self.init()

    def _find_block(self):
        pos_s = None
        pos_e = None
        self.f.seek(0)
        while True:
            line = self.f.readline()
            if line == self._start_label:
                if pos_s is None:
                    pos_s = self.f.tell()
                else:
                    raise ValueError('Multipy start label')
            if line == self._end_label:
                if pos_e is None:
                    pos_e = self.f.tell()
                else:
                    raise ValueError('Multipy end label')
            if len(line) == 0:
                break
        if pos_s is not None and pos_e is not None and pos_e < pos_s:
            raise ValueError('end before start')
        return pos_s, pos_e

    def load(self):
        self.f.seek(self.a)
        assert self.f.readline() == self._start_label
        while True:
            line = self.f.readline()
            if line == self._end_label:
                break
            if len(line) == 0:
                break
            spt = line.split()
            addr = spt[0].decode()
            name = spt[1].decode()
            self.d[name] = HostsItem(self.f.tell() - len(line), addr)
        assert self.f.tell() == self.b

    def init(self):
        a_, b_ = self._find_block()
        if a_ is None and b_ is None:
            if self.f.truncate() >= 1:
                self.f.seek(-2, 2)
                count = self.f.read(2).count(b'\n')
                if count != 2:
                    self.f.write(b'\n'*(2-count))
            self.a = self.f.tell()
            self.f.write(self._start_label)
            self.f.write(self._end_label)
            self.b = self.f.tell()
            self.flush()
        elif a_ is not None and b_ is not None:
            self.a = a_ - len(self._start_label)
            self.b = b_
            self.load()
        else:
            raise ValueError

    def _move(self, start, delta, size=-1):
        self.f.seek(start)
        data = self.f.read(size)
        self.f.seek(start + delta)
        self.f.write(data)
        self.f.truncate()

    # TODO: 用mtime判断文件是否被其他软件修改，如果修改则重新载入
    # TODO: 记录最后一次写入时间，以便查看
    def add(self, name, addr):
        assert is_ipv6(addr)
        line = f'{addr:39}\t{name}\n'.encode()
        pos = self.b - len(self._end_label)
        self.d[name] = HostsItem(pos, addr)
        self._move(pos, len(line))
        self.f.seek(pos)
        self.f.write(line)
        self.b += len(line)

    def remove(self, name):
        nt = self.d[name]
        # 检查
        self.f.seek(nt.pos)
        line = self.f.readline()
        readaddr, readname = line.split()
        assert readaddr == nt.addr.encode()
        assert readname == name.encode()
        # 向前移动数据，覆盖
        self._move(self.f.tell(), -len(line))
        self.b -= len(line)
        # 更新字典
        self.d.pop(name)
        for k, v in self.d.items():
            if v.pos > nt.pos:
                self.d[k] = HostsItem(v.pos-len(line), v.addr)

    def update(self, name, addr):
        assert is_ipv6(addr)
        # 更新字典
        old = self.d[name]
        self.d[name] = HostsItem(old.pos, addr)
        # 测试写入处的格式
        self.f.seek(old.pos)
        line = self.f.readline()
        assert line[39] == ord(b'\t')
        assert line[40:-1] == name.encode()
        # 写入内容
        self.f.seek(old.pos)
        baddr39 = addr.ljust(39).encode()
        self.f.write(baddr39)

    def auto_write(self, name, addr):
        if name in self.d:
            self.update(name, addr)
        else:
            self.add(name, addr)

    def flush(self):
        self.f.flush()
