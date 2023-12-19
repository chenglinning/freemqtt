# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from .packet import Packet
from .reason_code import Reason, validReasoneCode
from .pktype import PacketType
from .property import PropertSet, Property
from . import protocol, utils

class Pubrec(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Pubrec, self).__init__(ver, PacketType.PUBREC)
        self.rcode = Reason.Success
        self.propset = PropertSet(PacketType.PUBREC)

    def reason_code(self) -> Reason:
        return self.rcode
    
    def set_reason_code(self, rc: Reason) -> None:
        self.rcode = rc

    # unpack pubrec packet
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error(f"Error pubrec flags:{self.flags():02X}")
            return False
        pid = utils.read_int16(r)
        if pid is None:
            logging.error("Error pubrec packet id: None")
            return False
        self.set_pid(pid)

        if self.version == protocol.MQTT50 :
            # reason code
            rcode = utils.read_int8(r)
            if rcode is None:
                logging.error("Error pubrec packet reason code: None")
                return False
            if validReasoneCode(rcode, self.pktype):
                self.set_reason_code(Reason(rcode))
            else:
                logging.error(f"Invalid pubrec packet reason code: {rcode:02X}")
                return False

            # properties
            if not self.propset.unpack(r):
                logging.error("Error parsing properties")
                return False
        return True

    # pack pubrec packet
    def pack(self) -> bytes:
        w = io.BytesIO()
        # packet id
        utils.write_int16(w, self.pid)
        if self.version == protocol.MQTT50 :
            # reason code
            utils.write_int8(w, self.reason_code())
            # properties
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
        data = w.getvalue()
        w.close()
        return data