# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from .packet import Packet
from . import pktype, protocol, utils
from .property import PropertSet
from . import reason_code as ReasonCode

class Puback(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Puback, self).__init__(ver, pktype.PUBACK)
        self.rcode = 0
        self.propset = PropertSet(pktype.PUBACK)

    def reason_code(self) -> int:
        return self.rcode
    
    def set_reason_code(self, code: int) -> None:
        self.reason_code = code

    # unpack puback packet
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error("Error puback flags: %02X" % self.flags())
            return False

        pid = utils.read_int16(r)
        if pid is None:
            logging.error("Error puback packet id: None")
            return False
        self.set_pid(pid)

        if self.version == protocol.MQTT50 :
            # reason code
            rcode = utils.read_int8(r)
            if rcode is None:
                logging.error("Error puback packet reason code: None")
                return False
            if ReasonCode.valid4pktype(rcode, self.type):
                self.set_reason_code(rcode)
            else:
                logging.error("Invalid puback packet reason code: %02X" % rcode)
                return False
            # properties
            if not self.propset.unpack(r):
                logging.error("Error parsing properties.")
                return False
        return True

    # pack puback packet
    def pack(self) -> bytes:
        w = io.BytesIO()
        # packet id
        utils.write_int16(self.pid())

        if self.version == protocol.MQTT50 :
            # reason code
            utils.write_int8(self.reason_code())
            # properties
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
           
        data = w.getvalue()
        w.close()
        return data