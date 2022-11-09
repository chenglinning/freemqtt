# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from .packet import Packet
from . import pktype, protocol, utils

class Pingreq(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Pingreq, self).__init__(ver, pktype.PINGREQ)

    # unpack
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error("Error pingreq flags: %02X" % self.flags())
            return False
        data = utils.read_rest_data(r)
        if data:
            logging.error("Error pingreq packet")
            return False
        return True

    # pack
    def pack(self) -> bytes:
        return b""