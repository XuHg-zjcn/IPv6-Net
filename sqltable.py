#!/usr/bin/python3
'''
   Copyright 2021-2022 Xu Ruijun

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
'''

from collections.abc import Iterable
from numbers import Number

try:
    import numpy as np
except ModuleNotFoundError:
    def number_np2py(x):
        return x
else:
    def number_np2py(x):
        if isinstance(x, np.integer):
            x = int(x)
        elif isinstance(x, np.floating):
            x = float(x)
        return x


def onlyone_process(iterable,
                    def0=LookupError('not found'),
                    def2=LookupError('found multiply items')):
    def raise_return(x):
        if isinstance(x, Exception):
            raise x
        else:
            return x

    lst = list(iterable)
    if len(lst) == 0:
        return raise_return(def0)
    elif len(lst) == 1:
        return lst[0]
    else:
        return raise_return(def2)


class SqlTable:
    """
    Examples
    --------
    table_name: 'tab'
    name2type_dict: [('name','TEXT'), ('num','REAL')]
    """
    name2dtype = [('example_int', 'INT'), ('example_text', 'TEXT')]
    table_name = 'table_name'

    def __init__(self, conn, commit_each=False):
        self.conn = conn
        self.commit_each = commit_each
        self.create_table(commit=True)

    def create_table(self, commit=True):
        cur = self.conn.cursor()
        fields = []
        for name, dtype in self.name2dtype:
            if dtype:
                fields.append('{} {}'.format(name, dtype))
            else:
                fields.append(str(name))
        fields = ', '.join(fields)
        sql = 'CREATE TABLE IF NOT exists {}('\
              'id INTEGER PRIMARY KEY AUTOINCREMENT, {})'
        cur.execute(sql.format(self.table_name, fields))
        if commit or self.commit_each:
            self.conn.commit()

    def insert(self, values, commit=None):
        cur = self.conn.cursor()
        if not isinstance(values, dict):
            val_d = {}
            for v, (k, _) in zip(values, self.name2dtype):
                val_d[k] = v
        else:
            val_d = values
        sql = 'INSERT INTO {}({}) VALUES({})'
        sqf = sql.format(self.table_name,
                         ', '.join(val_d.keys()),
                         ('?,'*len(val_d))[:-1])
        cur.execute(sqf, list(val_d.values()))
        if commit or self.commit_each:
            self.conn.commit()

    def commit(self):
        """
        commit change to sqlite3 database.
        don't use in class method, please use 'self.conn.commit()'
        """
        if self.commit_each:
            raise RuntimeWarning('commit each change is Enable')
        self.conn.commit()

    @staticmethod
    def _fields2sql(fields=None):
        if isinstance(fields, str):
            fields_str = fields  # only one field, return without tuple
        elif isinstance(fields, Iterable):
            fields_str = ', '.join(fields)
        elif not fields:
            fields_str = '*'
        else:
            raise ValueError('invalid fields')
        return fields_str

    @staticmethod
    def _conds2where(cond_dict):
        """
        if cond_dict is empty, return empty string
        not empty dict, return string include 'WHERE'
        """
        if not cond_dict:
            return '', []
        sql = 'WHERE '
        paras = []
        for key, value in cond_dict.items():
            assert isinstance(key, str), 'conds dict keys must be str'
            value = number_np2py(value)
            if type(value) in [bool, int, float, str]:  # x == ?
                sql += '{}=? and '.format(key)
                paras.append(value)
            elif isinstance(value, tuple) and len(value) == 2:  # a <= x < b
                if type(value[0]) in [int, float]:
                    sql += '?<={0} and {0}<? and '.format(key)
                    paras += value
                elif isinstance(value[0], str):
                    if value[0] in ['<', '>', '>=', '<=', '=', '==', '!=']:
                        sql += '{}{}? and '.format(key, value[0])
                        paras.append(value[1])
                    elif value[0].upper() in ['GLOB', 'LIKE']:
                        sql += '{} {} "{}" and '.format(key, value[0].upper(), value[1])
                    else:
                        raise ValueError('invalid tuple first elem {}'.format(value[0]))
                else:
                    raise ValueError('invalid tuple {}'.format(value))
            elif isinstance(value, list):  # dict key as sql, without paras
                assert len(value) == key.count('?'),\
                    "counts '?' in key not same with length of paras"
                sql += key + ' and '
                paras += value
            else:
                raise ValueError('invalid value type {}'.format(type(value)))
            # TODO: append ' and ' here
        sql = sql[:-5]  # remove end of str ' and '
        return sql, paras

    def conds_sql(self, cond_dict=None, fields=None):
        """
        Get Plans matched conditions.
        :para cond_dict: {'field1':value,
                          'field2':(min, max),
                          'field3':('<', value), ...}
        :para fields: str single field,
                      list multiply fields,
                      None get all fields of table. 
        """
        fields_str = self._fields2sql(fields)
        where_str, paras = self._conds2where(cond_dict)
        sql = 'SELECT {} FROM {} {}'\
            .format(fields_str, self.table_name,where_str)
        return sql, paras

    def get_conds_execute(self, cond_dict=None, fields=None):
        cur = self.conn.cursor()
        sql, paras = self.conds_sql(cond_dict, fields)
        res = cur.execute(sql, paras)
        if isinstance(fields, str):
            return map(lambda x: x[0], res)
        else:
            return res

    def get_conds_onlyone(self, cond_dict, fields=None,
                          def0=LookupError('not found'),
                          def2=LookupError('found multiply items')):
        cur = self.get_conds_execute(cond_dict, fields)
        return onlyone_process(cur, def0, def2)

    def get_conds_onlyone_dict(self, cond_dict, fields=None,
                               def0=LookupError('not found'),
                               def2=LookupError('found multiply items')):
        assert not isinstance(fields, str),\
            "can't use single field str for return dict"
        fields = list(fields) if isinstance(fields, set) else fields
        c1 = self.get_conds_onlyone(cond_dict, fields, def0, def2)
        assert len(c1) == len(fields)
        return dict(zip(fields, c1))

    def _update2sql(self, update_dict):
        sqls = []
        paras = []
        for key, value in update_dict.items():
            value = number_np2py(value)
            if isinstance(value, Number) or \
               isinstance(value, str) or \
               isinstance(value, bytes):
                sqls.append("{}=?".format(key))
                paras.append(value)
            elif isinstance(value, tuple) and len(value) == 2 and isinstance(value[0], str):
                if value[0][-1] == '=':
                    sqls.append("{}={}{}?".format(key, key, value[0][:-1]))
                    paras.append(value[1])
                else:
                    sql.append("{}={}?".format(key, key, value[0]))
        return ', '.join(sqls), paras

    def update_conds(self, cond_dict, update_dict, commit=None):
        cur = self.conn.cursor()
        where_str, paras1 = self._conds2where(cond_dict)
        set_str, paras2 = self._update2sql(update_dict)
        sql = 'UPDATE {} SET {} {}'.format(self.table_name, set_str, where_str)
        cur.execute(sql, paras2+paras1)
        if self.commit_each or commit:
            self.conn.commit()

    def delete(self, cond_dict, commit=None):
        cur = self.conn.cursor()
        where_str, paras = self._conds2where(cond_dict)
        sql = 'DELETE FROM {} {}'.format(self.table_name, where_str)
        cur.execute(sql, paras)
        if self.commit_each or commit:
            self.conn.commit()

    def __del__(self):
        """
        auto commit when del SqlTable obj.
        """
        if not self.commit_each:
            self.conn.commit()
