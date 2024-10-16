# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from .packet import Packet
from .pktype import PacketType
from .property import PropertSet
from .reason_code import Reason, validReasoneCode
from . import protocol, utils
class Pubcomp(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Pubcomp, self).__init__(ver, PacketType.PUBCOMP)
        self.rcode = Reason.Success
        self.propset = PropertSet(PacketType.PUBCOMP)

    def reason_code(self) -> Reason:
        return self.rcode
    
    def set_reason_code(self, rc: Reason) -> None:
        self.rcode = rc

    # unpack pubcomp packet
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error(f"Error pubcomp flags:{self.flags():02X}")
            return False

        pid = utils.read_int16(r)
        if pid is None:
            logging.error("Error pubcomp packet id: None")
            return False
        self.set_pid(pid)
        
        if self.get_remain_len()==2: # no more data for this packet
            return True

        if self.version == protocol.MQTT50 :
            # reason code
            rcode = utils.read_int8(r)
            if rcode is None:
                logging.error("Error pubcomp packet reason code: None")
                return False
            if validReasoneCode(rcode, self.pktype):
                self.set_reason_code(Reason(rcode))
            else:
                logging.error(f"Invalid pubcomp packet reason code: {rcode:02X}")
                return False
            # properties
            if not self.propset.unpack(r):
                logging.error("Error parsing properties")
                return False
        return True

    # pack pubcomp packet
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