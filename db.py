#!/bin/python3
import sqlite3
from sqlfocus import SQLTable
import os
import re

conn = sqlite3.connect("data.db")

devices = SQLTable("devices", conn)
devices.create(exists=True, schema=(
    ("id", "INTEGER"),
    ("name", "TEXT"),  #名称
    ("mac", "TEXT"),  #MAC地址
    ("create_time", "DATETIME"),  #创建时间
))

ipaddrs = SQLTable("ipaddrs", conn)
ipaddrs.create(exists=True, schema=(
    ("id", "INTEGER"),
    ("devid", "INTEGER"),         #设备ID
    ("ipv4", "TEXT"),             #IPv4
    ("ipv6", "TEXT"),             #IPv6
    ("create_time", "DATETIME"),  #创建时间
    ("data_bytes", "INTEGER"),    #流量
    ("online_sec", "REAL"),       #在线时间(秒)
    ("conn_times", "INTEGER"),    #连接次数
    ("conn_last", "DATETIME"),    #最后一次连接时间
    ("update_last", "DATETIME"),  #最后一次更新地址时间
    ("update_times", "DATETIME")  #更新次数
))

with os.popen('ip neigh') as p:
    for line in p.readlines():
        addr, dev, port, lladdr, mac, state = line.split()
        print(devices.select(where=[devices.mac==mac]))
