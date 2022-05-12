import os
import stat

import ed25519


client_name = 'ipv6net_test'
hosts_file = '/etc/hosts'
hosts_block_name = 'IPv6Net'
domain_suffix = '.local'

udata_dir = 'data'
db_path = 'data/data.db'
key_path = 'data/key'

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
