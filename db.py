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
import sqlite3
from sqltable import SqlTable
import os
import re

class HostTable(SqlTable):
    table_name = 'host_table'
    name2dtype = [
    ("name", "TEXT"),             #设备名称
    ("ipv4", "TEXT"),             #IPv4
    ("ipv6", "TEXT"),             #IPv6
    ("online_sec", "REAL"),       #在线时间(秒)
    ("conn_count", "INTEGER"),    #连接次数
    ("conn_last", "REAL"),        #最后一次连接的时间戳
    ("update_last", "REAL"),      #最后一次更新地址的时间戳
    ("update_count", "INTEGER"),  #更新次数
    ("test_period", "REAL"),      #测试周期
    ("version", "INTEGER"),       #版本
    ("level", "INTEGER")          #等级
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_mono = {}

    def add_dev(self, name, ipv4, period=60.0):
        self.insert({'name':name,
                     'ipv4':ipv4,
                     'online_sec':0.0,
                     'conn_count':0,
                     'update_count':0,
                     'update_last':datetime.datetime.now(),
                     'update_count':0,
                     'test_period':period,
                     'version':0,
                     'level':0},
                    commit=True)

    def disconn(self, did):
        if did in self.last_mono:
            self.last_mono.pop(did)

    def inc_time(self, did):
        now = time.time()
        tmono = time.monotonic()
        if did not in self.last_mono:
            self.last_mono[did] = tmono
            self.update_conds({'id':did}, {'conn_count':('+=', 1), 'conn_last':now}, commit=True)
            return
        else:
            delta = tmono - self.last_mono[did]
            self.last_mono[did] = tmono
            self.update_conds({'id':did}, {'online_sec':('+=', delta), 'conn_last':now}, commit=True)

    def update_ipv6(self, did, ipv6, version):
        now = time.time()
        self.update_conds({'id':did},
                          {'update_count':('+=', 1),
                           'ipv6':str(ipv6),
                           'update_last':now,
                           'version':version},
                          commit=True)
