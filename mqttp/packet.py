# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0

import abc
import io
from . import mask, pktype, protocol

class Packet(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, ver: int=protocol.MQTT311, pktype:int=pktype.CONNECT) -> None:
        self.version = ver
        self.type = pktype
        self.pid = 0
        self.dup = False
        self.qos = protocol.QoS0
        self.retain = False

    # get payload of packet
    def payload(self) -> bytes:
        return bytearray()
    
    # get packet type
    def get_type(self) -> int:
        return self.type
    
    # get packet id
    def get_pid(self) -> int:
        return self.pid

    # set packet id
    def set_pid(self, pid: int) -> None:
        self.pid = pid
    
    #  set the packet is duplicate flag
    def set_dup(self, dup: bool) -> None:
        self.dup = dup
        
    #  return thether the packet is duplicate
    def get_dup(self) -> bool:
        return self._dup

    # Returns the MQTT Packet MQTT name
    def get_name(self) -> str:
        return pktype.PacketName(self.pktype)

    # Returns the Packet MQTT version 
    def get_version(self) -> int:
        return self.version

    # Returns the Packet MQTT version 
    def set_version(self, ver: int) -> None:
        self.version = ver

    # Set the packet's QoS
    def set_qos(self, qos: int) -> None:
        self.qos = qos

    # Return the packet's QoS
    def get_qos(self) -> int:
        return self.qos

    #  Set the packet's retain flag
    def set_retain(self, retain: bool) -> None:
        self.retain = retain
        
    #  return thether the packet retain flag
    def get_retain(self) -> bool:
        return self.retain

    # Parse the packet fixed header flags byte
    def parse_flags(self, flags: int) -> None:
        self.dup = flags & mask.Dup > 0
        self.qos = flags & mask.Qos >> 1
        self.retain = flags & mask.Retain > 0

    # Get fixed header first byte
    def fixed_header(self) -> int:
        return self.type << 4 | self.dup << 3 | self.qos << 1 | self.retain

    # Get fixed header flags
    def flags(self) -> int:
        return self.dup << 3 | self.qos << 1 | self.retain

    def unpack(self, r: io.BytesIO) -> bool:
        pass
    
    def pack(self) -> bytes:
        pass
    