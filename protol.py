#!/usr/bin/python3
from enum import Enum


class Commd(Enum):  #
    GTN = 0x00      # None
    PTN = 0x01      # str: name
    GTA = 0x02      # None
    PTA = 0x03      # >I:version, 16B:ipv6
    GTS = 0x04
    PTS = 0x05
    GOL = 0x06
    POL = 0x07
    GON = 0x08
    PON = 0x09
    GOA = 0x0A
    POA = 0x0B
    STAT = 0x0C      #
