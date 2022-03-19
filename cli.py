#!/usr/bin/python3
import datetime
import sys
from prettytable import PrettyTable
from db import htab

version_str = '''
版本v0.1.0-2
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
        tab = PrettyTable(fields)
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

