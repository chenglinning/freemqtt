# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from typing import List
from .packet import Packet
from . import pktype, protocol, utils
from .property import PropertSet
from . import reason_code as ReasonCode

class Unsuback(Packet):
    def __init__(self, ver:int=protocol.MQTT311, rcode_list: List[int]=[]) -> None:
        super(Unsuback, self).__init__(ver, pktype.UNSUBACK)
        self.rcode_list: List[int] = rcode_list
        self.propset = PropertSet(pktype.UNSUBACK)

    # unpack packet
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error("Error suback flags: %02X" % self.flags())
            return False
        # packet id
        pid = utils.read_int16(r)
        if pid is None:
            logging.error("Error suback packet id: None")
            return False
        self.set_pid(pid)
        # properties
        if self.version == protocol.MQTT50 :
            if not self.propset.unpack(r):
                logging.error("Error parsing properties.")
                return False
        # reason code list
        while True:
            rcode = utils.read_int8(r)
            if rcode is None:
                logging.error("Error suback reason code: None")
                return False
            if ReasonCode.valid4pktype(rcode, self.get_type()):
                self.rcode_list.append(rcode)
            else:
                logging.error("Invalid suback reason code: %02X" % rcode)
                return False

        # valid payload
        if len(self.rcode_list) == 0:
            logging.error("No reason code in payload.")
            return False
            
        return True

    # pack packet
    def pack(self) -> bytes:
        w = io.BytesIO()
        # packet id
        utils.write_int16(self.pid())
    	# property
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)

        # payload (reason code list)
        for rc in self.rcode_list:
            utils.write_int8(w, rc)            
        data = w.getvalue()
        w.close()
        return data