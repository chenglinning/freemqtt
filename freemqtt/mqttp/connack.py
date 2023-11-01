# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
from re import U
from .packet import Packet
from . import mask, protocol, utils
from .pktype import PacketType
from .property import PropertSet, Property, StringPair
from .reason_code import Reason, validReasoneCode
class Connack(Packet):
    def __init__(self, ver:int=protocol.MQTT311) -> None:
        super(Connack, self).__init__(ver, PacketType.CONNACK)
        self.ack_flags = 0
        self.rcode = Reason.Success
        self.propset = PropertSet(PacketType.CONNACK)

    def reason_code(self) -> Reason:
        return self.rcode
    
    def ack_flags(self) -> int:
        return self.ack_flags
    
    def set_ack_flags(self, flags: int) -> None:
        self.ack_flags = flags
        
    def set_reason_code(self, rc: Reason) -> None:
        self.rcode = rc

    def session_present(self) -> bool:
        return self.flags & mask.SessionPresent > 0

    def set_session_present(self, present: bool) -> None:
        if present:
            self.ack_flags |= mask.SessionPresent
        else:
            self.ack_flags &= ~mask.SessionPresent

    # set properties for connack
    def set_session_expiry_interval(self, v) -> bool:
        return self.propset.set(Property.Session_Expiry_Interval, v)

    def set_receive_maximum(self, v: int) -> bool:
        return self.propset.set(Property.Receive_Maximum, v)

    def set_maximum_qos(self, v: int) -> bool:
        return self.propset.set(Property.Maximum_QoS, v)

    def set_retain_available(self, v: int) -> bool:
        return self.propset.set(Property.Retain_Available, v)

    def set_maximum_packet_size(self, v: int) -> bool:
        return self.propset.set(Property.Maximum_Packet_Size, v)

    def set_assiged_client_identifier(self, v: str) -> bool:
        return self.propset.set(Property.Assigned_Client_Identifier, v)

    def set_topic_alias_maximum(self, v: int) -> bool:
        return self.propset.set(Property.Topic_Alias_Maximum, v)

    def set_reason_string(self, v: str) -> bool:
        return self.propset.set(Property.Reason_String, v)

    def set_user_property(self, k: str, v: str) -> bool:
        sp = StringPair(k,v)
        return self.propset.set(Property.User_Property, sp)

    def set_wildcard_subscription_available(self, v: int) -> bool:
        return self.propset.set(Property.Wildcard_Subscription_Available, v)

    def set_subscription_identifiers_available(self, v: int) -> bool:
        return self.propset.set(Property.Subscription_Identifier_Available, v)

    def set_shared_subscription_available(self, v: int) -> bool:
        return self.propset.set(Property.Shared_Subscription_Available, v)

    def set_server_keep_alive(self, v: int) -> bool:
        return self.propset.set(Property.Server_Keep_Alive, v)

    def set_response_information(self, v: str) -> bool:
        return self.propset.set(Property.Response_Information, v)

    def set_server_reference(self, v: str) -> bool:
        return self.propset.set(Property.Server_Reference, v)

    def set_authentication_method(self, v: str) -> bool:
        return self.propset.set(Property.Authentication_Method, v)

    def set_authentication_data(self, v: bytes) -> bool:
        return self.propset.set(Property.Authentication_Data, v)

    # unpanc connack packet on client side
    def unpack(self, r: io.BytesIO) -> bool:
        if self.flags() != 0x00:
            logging.error(f"Error connack flags: {self.flags():02X}")
            return False
        
        ack_flags = utils.read_int8(r)
        if ack_flags is None:
            logging.error("Error connack flags: None")
            return False
        if not (ack_flags==0x00 or ack_flags==0x01):
            logging.error(f"Error connack flags: {ack_flags:02X}")
            return False
        self.ack_flags = ack_flags

        rcode = utils.read_int8(r)
        if rcode is None:
            logging.error("Error connack reason code: None")
            return False
        if validReasoneCode(rcode, self.pktype):
            self.rcode = Reason(rcode)
        else:
            logging.error(f"Error connack reason code: {rcode:02X}")
            return False

        if self.version == protocol.MQTT50 :
            # properties
            self.propset = PropertSet(PacketType.CONNACK)
            if not self.propset.unpack(r):
                logging.error("Error parsing properties.")
                return False
        return True

    # pack
    def pack(self) -> bytes:
        w = io.BytesIO()
        # ack flags
        utils.write_int8(w,self.ack_flags)
    	# reason code
        utils.write_int8(w, self.rcode)
    	# property
        if self.version == protocol.MQTT50:
            ppdata = self.propset.pack()
            plen = len(ppdata)
            utils.write_uvarint(w, plen)
            utils.write_bytes(w, ppdata)
        data = w.getvalue()
        w.close()
        return data
