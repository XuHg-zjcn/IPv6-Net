#!/usr/bin/python3
########################################################################
'''守护进程'''
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
import socket
import logging

import ip46
import server
import tester
import syncer
import peer


if __name__ == '__main__':
    if os.isatty(1):
        logging.basicConfig(level=logging.DEBUG)
    ipmon = ip46.IPMon()
    ipmon.start()
    Server4 = server.Server(ipmon.stat4, peer.peerdict.find_v4)
    Server4.start()
    Server6 = server.Server(ipmon.stat6, peer.peerdict.find_v6)
    Server6.start()
    syncth = syncer.SyncThread(ipmon.stat6)
    syncth.start()
    Tester = tester.Tester(ipmon.stat6, syncth)
    Tester.start()
