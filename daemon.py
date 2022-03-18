#!/usr/bin/python3
import threading

import ip46
import syncer


if __name__ == '__main__':
   th_server = threading.Thread(target=ip46.ServerUDP)
   th_server.start()
   Syncer = syncer.Syncer()
   Syncer.start_all()
