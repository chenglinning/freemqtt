# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
RESERVED = 0
CONNECT = 1
CONNACK = 2
PUBLISH = 3
PUBACK = 4
PUBREC = 5
PUBREL = 6
PUBCOMP = 7
SUBSCRIBE = 8
SUBACK = 9
UNSUBSCRIBE = 10
UNSUBACK = 11
PINGREQ = 12
PINGRESP = 13
DISCONNECT = 14
AUTH = 15
WILLPP = 32

PacketNames = {
    RESERVED:   "RESERVED", 
    CONNECT:    "CONNECT", 
    CONNACK:    "CONNACK", 
    PUBLISH:    "PUBLISH", 
    PUBACK:     "PUBACK", 
    PUBREC:     "PUBREC", 
    PUBREL:     "PUBREL",
    PUBCOMP:    "PUBCOMP",
    SUBSCRIBE:  "SUBSCRIBE",
    SUBACK:     "SUBACK", 
    UNSUBSCRIBE:"UNSUBSCRIBE",
    UNSUBACK:   "UNSUBACK",
    PINGREQ:    "PINGREQ",
    PINGRESP:   "PINGRESP",
    DISCONNECT: "DISCONNECT",
    AUTH: "AUTH", 
#   WILLPP: "WILL MESSAGE",
}

def PacketName(pktype: int) -> str:
    return PacketNames[pktype]
