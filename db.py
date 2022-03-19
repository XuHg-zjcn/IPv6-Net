#!/bin/python3
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
                     'test_period':period},
                    commit=True)

    def disconn(self, did):
        if did in self.last_tmono:
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

    def update_ipv6(self, did, ipv6):
        now = time.time()
        self.update_conds({'id':did}, {'update_count':('+=', 1), 'ipv6':ipv6, 'update_last':now}, commit=True)

conn = sqlite3.connect('data.db')
htab = HostTable(conn)
