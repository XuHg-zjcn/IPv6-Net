#!/usr/bin/python3
from enum import Enum


class Commd(Enum):  #
    GTN = 0x00      # None
    GTA = 0x01      # None
    POA = 0x03      # idnefer(4B), version(4B), ipv6(16B)
