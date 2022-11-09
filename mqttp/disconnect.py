# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from re import U
from .packet import Packet
from . import mask, pktype, protocol, utils
from .property import PropertSet
from . import reason_code as ReasonCode

class Disconnect(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Disconnect, self).__init__(ver, pktype.DISCONNECT)
        self.rcode = ReasonCode.Success
        self.propset = PropertSet(pktype.DISCONNECT)

    def reason_code(self) -> int:
        return self.rcode

    def set_reason_code(self, code: int) -> None:
        self.rcode = code

    # unpanc
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error("Error disconnect flags: %02X" % self.flags())
            return False
        rcode = utils.read_int8(r)
        if rcode is None:
            logging.error("Error disconnect reason code: None")
            return False
        if ReasonCode.valid4pktype(rcode, self.type()):
            self.rcode = rcode
        else:
            logging.error("Error disconnnet reason code: %02X" % rcode)
            return False
        if self.version == protocol.MQTT50 :
            # properties
            self.propset = PropertSet(pktype.CONNACK)
            if not self.propset.unpack(r):
                logging.error("Error parsing properties.")
                return False
        return True

    # pack
    def pack(self) -> bytes:
        w = io.BytesIO()
    	# reason code
        utils.write_int8(self.rcode)
    	# property
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
        data = w.getvalue()
        w.close()
        return data
