# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from .packet import Packet
from . import pktype, protocol, utils
from .property import PropertSet, Authentication_Method, Authentication_Data
from . import reason_code as ReasonCode

class Auth(Packet):
    def __init__(self, ver:int=protocol.MQTT50) -> None:
        super(Auth, self).__init__(ver, pktype.AUTH)
        self.rcode = 0
        self.propset = PropertSet(pktype.AUTH)

    def reason_code(self) -> int:
        return self.rcode

    def set_reason_code(self, code: int) -> None:
        self.rcode = code

    def method(self) -> str:
        return self.propset.props.get(Authentication_Method, None)

    def set_method(self, method: str) -> bool:
        return self.propset.set(Authentication_Method, method)

    def data(self) -> bytes:
        return self.propset.props.get(Authentication_Data, None)

    def set_data(self, data: bytes) -> bool:
        return self.propset.set(Authentication_Data, data)

    # unpack
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error("Error connack flags: %02X" % self.flags())
            return False

        rcode = utils.read_int8(r)
        if rcode is None:
            logging.error("Error AUTH reason code: None")
            return False
        if ReasonCode.valid4pktype(rcode, self.type()):
            self.rcode = rcode
        else:
            logging.error("Error AUTH reason code: %02X" % rcode)
            return False

        if self.version == protocol.MQTT50 :
            # properties
            self.propset = PropertSet(pktype.AUTH)
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
