import socket
import os

def get_desc():
    p = os.popen("ifconfig")
    devs = p.read().split('\n\n')
    dv = []
    for dev in devs:
        if not dev:
            break
        lines = dev.split('\n')
        line0 = lines[0].split()
        if "LOOPBACK" in line0[1]:
            continue
        tmp = [line0[0]]
        for line in lines[1:]:
            w = line.split()
            tp, addr = w[:2]
            if tp in {'inet', 'ether'} or '<global>' in line:
                tmp.append(f'{tp} {addr}')
        dv.append('\n'.join(tmp))
    return '\n\n'.join(dv)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def server():
    s.bind(('0.0.0.0', 4646))
    s.listen(1)
    while True:
        s1, addr = s.accept()
        s1.send(get_ipv6().encode())
        print(addr)
        s1.close()

def client(ipv4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ipv4, 4646))
    r = s.recv(10000)
    s.close()
    print(r.decode())
