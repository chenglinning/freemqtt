# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0

import io
import logging
from .packet import Packet
from . import protocol, utils
from .pktype import PacketType
from .property import PropertSet, Property
from .reason_code import Reason, validReasoneCode
class Auth(Packet):
    def __init__(self, ver:int=protocol.MQTT50) -> None:
        super(Auth, self).__init__(ver, PacketType.AUTH)
        self.rcode = Reason.Success
        self.propset = PropertSet(PacketType.AUTH)

    def reason_code(self) -> Reason:
        return self.rcode

    def set_reason_code(self, rc: Reason) -> None:
        self.rcode = rc

    def method(self) -> str:
        return self.propset.props.get(Property.Authentication_Method, None)

    def set_method(self, method: str) -> bool:
        return self.propset.set(Property.Authentication_Method, method)

    def data(self) -> bytes:
        return self.propset.props.get(Property.Authentication_Data, None)

    def set_data(self, data: bytes) -> bool:
        return self.propset.set(Property.Authentication_Data, data)

    # unpack
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error(f"Error connack flags: {self.flags():02X}")
            return False

        rcode = utils.read_int8(r)
        if rcode is None:
            logging.error("Error AUTH reason code: None")
            return False
        if validReasoneCode(rcode, self.pktype):
            self.rcode = Reason(rcode)
        else:
            logging.error(f"Error AUTH reason code: {rcode:02X}")
            return False

        if self.version == protocol.MQTT50 :
            # properties
            self.propset = PropertSet(PacketType.AUTH)
            if not self.propset.unpack(r):
                logging.error("Error parsing properties")
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
