#!/usr/bin/python3
from enum import Enum


class Commd(Enum): # Params
    GN = 0x00      #
    PN = 0x01      # Ver, Len, Name, Sign
    GA = 0x02      #
    PA = 0x03      # Ver, IPv6, Sign
    GK = 0x04      #
    PK = 0x05      # Pub
    GI = 0x06      #
    PI = 0x07      # Ver, Len, Info, Sign
    GL = 0x08      #
    PL = 0x09      #
    TG = 0x0A      # Pub
    NF = 0x0B      #
    STAT = 0x0C    #
