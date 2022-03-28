#!/usr/bin/python3
########################################################################
'''CLI交互操作数据库'''
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
import datetime
import sys
import sqlite3

from prettytable import PrettyTable

from db import HostTable


conn = sqlite3.connect('data.db')
htab = HostTable(conn)

version_str = '''
IPv6Net v0.1.0-3
Copyright (C) 2022  Xu Ruijun
许可证 GPLv3+：GNU 通用公共许可证第 3 版或更新版本。
本程序是自由软件：您可以自由修改和重新发布它。
在法律范围内没有任何担保。
'''

def ts2str(x):
    if x is None:
        return ''
    else:
        x = datetime.datetime.fromtimestamp(x)
        return x.strftime("%Y-%m-%d %H:%M:%S")

def isExists(name):
    res = htab.get_conds_execute(cond_dict={'name':name})
    res = list(res)
    return len(res) != 0

def cli():
    s = input('请选择[1.添加 2.查看 3.修改 4.删除 v.版本]:')
    if s == '1':
        name = input('请输入设备名称:')
        ipv4 = input('请输入局域网IPv4:')
        period = input('请输入测试周期(单位秒,默认60秒):')
        try:
            period = float(period)
        except Exception:
            period = 60.0
        htab.add_dev(name, ipv4, period)
    elif s == '2':
        fields = ['name', 'ipv4', 'ipv6', 'online_sec',
                  'conn_last', 'conn_count']
        res = htab.get_conds_execute(fields=fields)
        res = map(lambda x:(*x[:3], int(x[3]),
                            ts2str(x[4]), int(x[5])), res)
        tab = PrettyTable()
        tab.add_column('name', [], align='l')
        tab.add_column('ipv4', [], align='l')
        tab.add_column('ipv6', [], align='l')
        tab.add_column('online_sec', [], align='r')
        tab.add_column('conn_last', [], align='l')
        tab.add_column('conn_count', [], align='r')
        tab.add_rows(res)
        print(tab)
    elif s == '3':
        name = input('请输入要修改的设备名称:')
        if not isExists(name):
            print('该名称的设备不存在')
            return
        ipv4 = input('请输入局域网IPv4:')
        update_dict = {'ipv4':ipv4}
        period = input('请输入测试周期(单位秒,默认不改变):')
        try:
            period = float(period)
        except Exception:
            pass
        else:
            update_dict['period'] = period
        htab.update_conds(cond_dict={'name':name},
                         update_dict=update_dict,
                         commit=True)
    elif s == '4':
        name = input('请输入要删除的设备名称:')
        if not isExists(name):
            print('该名称的设备不存在')
        else:
            htab.delete({'name':name}, commit=True)
    elif s == 'v':
        print(version_str)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        cli()

