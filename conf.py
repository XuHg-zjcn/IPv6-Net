import os

client_name = 'ipv6net_test'
hosts_file = '/etc/hosts'
domain_suffix = '.local'

udata_dir = 'data'
db_path = 'data/data.db'

if not os.path.exists(udata_dir):
    os.makedirs(udata_dir)
