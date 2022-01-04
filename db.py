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

    def add_dev(self, name, ipv4, period=60.0):
        self.insert({'name':name,
                     'ipv4':ipv4,
                     'online_sec':0.0,
                     'conn_count':0,
                     'update_count':0,
                     'update_last':datetime.datetime.now(),
                     'update_count':0,
                     'test_period':period})
        self.commit()

    def conn_on(self, did):
        now = time.time()
        self.update_conds({'id':did}, {'conn_count':('+=', 1), 'conn_last':now})
        self.commit()

    def inc_time(self, did):
        now = time.time()
        sec, last = self.get_conds_onlyone({'id':did}, fields=('online_sec', 'conn_last'))
        if last is not None:
            sec += now-last
        else:
            sec = 0
        self.update_conds({'id':did}, {'online_sec':sec, 'conn_last':now})
        self.commit()

    def update_ipv6(self, did, ipv6):
        now = time.time()
        self.update_conds({'id':did}, {'conn_count':('+=', 1), 'ipv6':ipv6, 'update_last':now})
        self.commit()

conn = sqlite3.connect('data.db')
htab = HostTable(conn)

