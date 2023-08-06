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

import conf
import ip46
import server
import tester
import syncer
import peer


if __name__ == '__main__':
    logg_level = conf.logg_level_tty if os.isatty(1) else conf.logg_level_bkgd
    logg_filename = None if os.isatty(1) else conf.logg_path
    logging.basicConfig(filename=logg_filename,
                        format=conf.logg_format,
                        datefmt=conf.logg_datefmt,
                        level=logg_level)
    ipmon = ip46.IPMon()
    ipmon.start()
    peer.Peer.sock4 = ipmon.stat4
    peer.Peer.sock6 = ipmon.stat6
    syncth = syncer.SyncThread(ipmon.stat4, ipmon.stat6)
    syncth.start()
    peer.Peer.syncth = syncth
    Server4 = server.Server(ipmon.stat4, peer.peerdict.find_v4)
    Server4.start()
    Server6 = server.Server(ipmon.stat6, peer.peerdict.find_v6)
    Server6.start()
    Tester = tester.Tester(ipmon.stat4, ipmon.stat6, syncth)
    Tester.start()
