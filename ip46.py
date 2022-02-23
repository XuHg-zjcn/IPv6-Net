#!/usr/bin/python3
import socket
import os

#TODO: add sign
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

def ServerTCP():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('0.0.0.0', 4646))
    s.listen(1)
    while True:
        s1, addr = s.accept()
        s1.send(get_desc().encode())
        print(addr)
        s1.close()

def ClientTCP(ipv4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ipv4, 4646))
    r = s.recv(10000)
    s.close()
    return r.decode()

def ServerUDP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('0.0.0.0', 4646))
    while True:
        data, addr = s.recvfrom(1000)
        s.sendto(get_desc().encode(), addr)
        print(addr)

def ClientUDP(ipv4, timeout=10):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    s.sendto(b'', (ipv4, 4646))
    r = s.recv(10000)
    s.close()
    return r.decode()


if __name__ == '__main__':
    ServerUDP()
