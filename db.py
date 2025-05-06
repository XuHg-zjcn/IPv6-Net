#!/bin/python3
########################################################################
'''数据库操作'''
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
import datetime
import ipaddress

from hashlib import sha256
import ed25519

from sqltable import SqlTable
import conf
import ip46


class HostTable(SqlTable):
    table_name = 'host_table'
    name2dtype = [
        ("name", "TEXT"),             # 设备名称
        ("pubkey", "BLOB"),           # Ed25519
        ("ipv4", "TEXT"),             # IPv4
        ("ipv6", "TEXT"),             # IPv6
        ("addr_sign", "BLOB"),        # 签名
        ("online_sec", "REAL"),       # 在线时间(秒)
        ("conn_count", "INTEGER"),    # 连接次数
        ("conn_last", "REAL"),        # 最后一次连接的时间戳
        ("update_last", "REAL"),      # 最后一次更新地址的时间戳
        ("update_count", "INTEGER"),  # 更新次数
        ("test_period", "REAL"),      # 测试周期
        ("version", "INTEGER"),       # 版本
        ("level", "INTEGER"),         # 等级
        ("lst_ver", "INTEGER"),       # 交换列表版本
        ("lst_date", "INTEGER"),      # 交换列表日期
        ("lst_hash", "BLOB"),         # 交换列表哈希
        ("lst_notify", "BOOL"),       # 是否需要通知对方更新交换列表
    ]
    # TODO: 保存对方知道自己的版本

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ipv4, ipv6 = ip46.get_local_addr()
        if self.get_conds_onlyone({'id': 0}, def0=0, def2=2) == 0:
            self.insert({'id': 0,
                         'name': conf.client_name,
                         'pubkey': conf.vk.to_bytes(),
                         'ipv4': str(ipv4),
                         'online_sec': 0.0,
                         'conn_count': 0,
                         'update_count': 0,
                         'update_last': datetime.datetime.now(),
                         'update_count': 0,
                         'test_period': 60.0,
                         'version': 0,
                         'level': 0},
                        commit=True)
        self.last_mono = {}

    def add_dev(self, name, ipv4, ipv6, pubkey=None, period=60.0):
        assert isinstance(name, str)
        assert isinstance(period, float)
        insert_dict = {'name': name,
                       'online_sec': 0.0,
                       'conn_count': 0,
                       'update_count': 0,
                       'update_last': datetime.datetime.now(),
                       'update_count': 0,
                       'test_period': period,
                       'version': 0,
                       'level': 0}
        if ipv4:
            assert isinstance(ipv4, ipaddress.IPv4Address)
            insert_dict['ipv4'] = ipv4.compressed
        if ipv6:
            assert isinstance(ipv6, ipaddress.IPv6Address)
            insert_dict['ipv6'] = ipv6.compressed
        if pubkey:
            assert isinstance(pubkey, ed25519.keys.VerifyingKey)
            insert_dict['pubkey'] = pubkey.to_bytes()
        self.insert(insert_dict, commit=True)

    def disconn(self, did):
        if did in self.last_mono:
            self.last_mono.pop(did)

    def inc_time(self, did, ts=None):
        if ts is None:
            ts = time.time()
        tmono = time.monotonic()
        if did not in self.last_mono:
            self.last_mono[did] = tmono
            self.update_conds({'id': did},
                              {'conn_count': ('+=', 1),
                               'conn_last': ts},
                              commit=True)
            return
        else:
            delta = tmono - self.last_mono[did]
            self.last_mono[did] = tmono
            self.update_conds({'id': did},
                              {'online_sec': ('+=', delta),
                               'conn_last': ts},
                              commit=True)

    def update_ipv6(self, did, ipv6, version, sign=None):
        now = time.time()
        self.update_conds({'id': did},
                          {'update_count': ('+=', 1),
                           'ipv6': str(ipv6),
                           'update_last': now,
                           'version': version,
                           'addr_sign': sign},
                          commit=True)

class ExchangeTable(SqlTable):
    table_name = 'exchange_table'
    name2dtype = [
        ('info_id', 'INTEGER'),   # 待交换信息的节点ID
        ('peer_id', 'INTEGER'),   # 交换对方的节点ID
        ('peer_ver', 'INTEGER'),  # 已知交换对方的版本, 空值表示待通知添加, -1待删除
    ]

    def get_listhash(peer_id):
        h = sha256()
        cur = self.conn.cursor()
        res = cur.execute('SELECT pubkey FROM host_table '
                          f'WHEN id IN (SELECT info_id FROM exchange_table WHERE peer_id={peer_id}) '
                          'ORDER BY pubkey ASC')
        for pubkey in res:
            h.update(pubkey)
        return h.digest()

    def get_notifyinfo(self, peer_id):
        hlist = sha256()
        hinfo = sha256()
        cur = self.conn.cursor()
        res = cur.execute('SELECT pubkey, version, ipv6, addr_sign, peer_ver '
                          'FROM exchange_table INNER JOIN host_table '
                          'ON host_table.id=exchange_table.info_id '
                          'WHERE peer_id=? '
                          'ORDER BY pubkey ASC',
                          peer_id)
        addrm = []
        update = []
        for pubkey, version, ipv6, addr_sign, peer_ver in res:
            if peer_ver < 0:
                addrm.append(bytes([Commd.RMEXC.value]) + pubkey)
                continue
            if peer_ver is None:
                addrm.append(bytes([Commd.ADDEXC.value]) + pubkey)
            info = bytes([Commd.PK.value]) + pubkey \
                   + bytes([Commd.PA.value]) + version.to_bytes(8, 'big') + ipaddress.IPv6Address(ipv6).packed
            hlist.update(pubkey)
            hinfo.update(info)
            if peer_ver is None or peer_ver < version:
                update.append(info)
        return b''.join(addrm) + b''.join(update)

    def set_update(self, info_id):
        cur = self.conn.cursor()
        res = cur.execute('UPDATE host_table SET lst_notify=1 '
                          f'WHERE id IN (SELECT peer_id FROM exchange_table WHERE info_id={info_id})')
        peers = self.get_conds_execute(cond_dict={'info_id':info_id}, fields='peer_id')
        return list(peers)

    def set_peer_ver(self, info_id, peer_id, peer_ver):
        self.update_conds({'info_id':info_id, 'peer_id':peer_id}, {'peer_ver':peer_ver})
