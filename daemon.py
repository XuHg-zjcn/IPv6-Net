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
import socket

import server
import tester
import peer


if __name__ == '__main__':
   sock6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
   sock6.bind(('::', 4646))
   Server6 = server.Server(sock6, peer.peerdict.find_v46)
   Server6.start()
   Tester = tester.Tester(sock6)
   Tester.start()
