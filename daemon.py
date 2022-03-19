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
import threading

import ip46
import syncer


if __name__ == '__main__':
   th_server = threading.Thread(target=ip46.ServerUDP)
   th_server.start()
   Syncer = syncer.Syncer()
   Syncer.start_all()
