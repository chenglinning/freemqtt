# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from re import U
from .packet import Packet
from . import protocol, utils

from .pktype import PacketType
from .property import PropertSet, Property, StringPair
from .reason_code import Reason, validReasoneCode

class Disconnect(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Disconnect, self).__init__(ver, PacketType.DISCONNECT)
        self.rcode = Reason.Success
        self.propset = PropertSet(PacketType.DISCONNECT)

    def reason_code(self) -> Reason:
        return self.rcode

    def set_reason_code(self, code: Reason) -> None:
        self.rcode = code

    # set properties for disconnet
    def set_session_expiry_interval(self, v) -> bool:
        return self.propset.set(Property.Session_Expiry_Interval, v)
    def set_reason_string(self, v: str) -> bool:
        return self.propset.set(Property.Reason_String, v)
    def set_user_property(self, k: str, v: str) -> bool:
        sp = StringPair(k,v)
        return self.propset.set(Property.User_Property, sp)
    
    # get properties for disconnet
    def session_expiry_interval(self) ->int:
        sei = self.propset.get(Property.Session_Expiry_Interval)
        return  sei if sei else 0

    # unpack
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error(f"Error disconnect flags: {self.flags():02X}")
            return False
        
        if self.version == protocol.MQTT311:
            return True
        
        if self.version == protocol.MQTT50:
            rcode = utils.read_int8(r)
            if rcode is None:
                logging.info("Disconnect reason code: None")
                return True
            if validReasoneCode(rcode, self.pktype):
                self.rcode = Reason(rcode)
            else:
                logging.error(f"Error disconnnet reason code:{rcode:02X}")
                return False
            # properties
            self.propset = PropertSet(PacketType.DISCONNECT)
            if not self.propset.unpack(r):
                logging.error("Error parsing properties")
                return False
        return True

    # pack
    def pack(self) -> bytes:
        w = io.BytesIO()
    	# property
        if self.version == protocol.MQTT50:
            # reason code
            utils.write_int8(w, self.rcode)
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
        data = w.getvalue()
        w.close()
        return data
