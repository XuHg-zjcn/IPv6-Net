#!/usr/bin/python3
########################################################################
'''配置参数设置和初始化key'''
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
import os
import sys
import stat

import ed25519


client_name = 'ipv6net_test'
hosts_file = '/etc/hosts'
hosts_block_name = 'IPv6Net'
domain_suffix = '.local'

udata_dir = 'data'
db_path = 'data/data.db'
key_path = 'data/key'

os.chdir(os.path.dirname(sys.argv[0]))
if not os.path.exists(udata_dir):
    os.makedirs(udata_dir)

if not os.path.exists(key_path):
    sk, vk = ed25519.create_keypair()
    with open(key_path, 'wb') as f:
        os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)
        f.write(sk.to_ascii(encoding='base64'))
else:
    with open(key_path, 'rb') as f:
        k64 = f.read()
    k = ed25519.from_ascii(k64, encoding='base64')
    sk = ed25519.SigningKey(k)
    vk = sk.get_verifying_key()
    del k, k64
