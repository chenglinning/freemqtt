# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
from typing import Any
from .utils import * 
from .pktype import *

One_Byte = 0
Two_Byte_Integer = 1
Four_Byte_Integer = 2
Variable_Byte_Integer = 3
UTF8_String = 4
UTF8_String_Pair = 5
Binary_Data = 6

Payload_Format_Indicator          = 0x01
Message_Expiry_Interval           = 0x02
Content_Type                      = 0x03
Response_Topic                    = 0x08
Correlation_Data                  = 0x09
Subscription_Identifier           = 0x0B
Session_Expiry_Interval		      = 0x11
Assigned_Client_Identifier        = 0x12
Server_Keep_Alive                 = 0x13
Authentication_Method             = 0x15
Authentication_Data               = 0x16
Request_Problem_Information       = 0x17
Will_Delay_Interval               = 0x18
Request_Response_Information      = 0x19
Response_Information              = 0x1A
Server_Reference                  = 0x1C
Reason_String                     = 0x1F
Receive_Maximum                   = 0x21
Topic_Alias_Maximum               = 0x22
Topic_Alias                       = 0x23
Maximum_QoS                       = 0x24
Retain_Available                  = 0x25
User_Property                     = 0x26
Maximum_Packet_Size               = 0x27
Wildcard_Subscription_Available   = 0x28
Subscription_Identifier_Available = 0x29
Shared_Subscription_Available     = 0x2A

propertyTypeMap =  {
    Payload_Format_Indicator:			One_Byte,
    Message_Expiry_Interval:            Four_Byte_Integer,
    Content_Type:                    	UTF8_String,
    Response_Topic:                  	UTF8_String,
    Correlation_Data:                	Binary_Data,
    Subscription_Identifier:         	Variable_Byte_Integer,
    Session_Expiry_Interval:		    Four_Byte_Integer,
    Assigned_Client_Identifier:         UTF8_String,
    Server_Keep_Alive:                  Two_Byte_Integer,
    Authentication_Method:              UTF8_String,
    Authentication_Data:                Binary_Data,
    Request_Problem_Information:        One_Byte,
    Will_Delay_Interval:                Four_Byte_Integer,
    Request_Response_Information:       One_Byte,
    Response_Information:               UTF8_String,
    Server_Reference:                   UTF8_String,
    Reason_String:                      UTF8_String,
    Receive_Maximum:                    Two_Byte_Integer,
    Topic_Alias_Maximum:                Two_Byte_Integer,
    Topic_Alias:                        Two_Byte_Integer,
    Maximum_QoS:                        One_Byte,
    Retain_Available:                   One_Byte,
    User_Property:                      UTF8_String_Pair,
    Maximum_Packet_Size:                Four_Byte_Integer,
    Wildcard_Subscription_Available:    One_Byte,
    Subscription_Identifier_Available:  One_Byte,
    Shared_Subscription_Available:      One_Byte,
}

# propertyAllowedMessageTypes properties and their supported packets type.
# bool flag indicates either duplicate allowed or not
propertyAllowedMessageTypes = {
	Payload_Format_Indicator:            {PUBLISH: False, WILLPP: False},
	Message_Expiry_Interval:             {PUBLISH: False, WILLPP: False},
	Content_Type:                        {PUBLISH: False, WILLPP: False},
	Response_Topic:                      {PUBLISH: False, WILLPP: False},
	Correlation_Data:                    {PUBLISH: False, WILLPP: False},
	Subscription_Identifier:             {PUBLISH: True, SUBSCRIBE: False},
	Session_Expiry_Interval:             {CONNECT: False, CONNACK: False, DISCONNECT: False},
	Assigned_Client_Identifier:          {CONNACK: False},
	Server_Keep_Alive:                   {CONNACK: False},
	Authentication_Method:               {CONNECT: False, CONNACK: False, AUTH: False},
	Authentication_Data:                 {CONNECT: False, CONNACK: False, AUTH: False},
	Request_Problem_Information:         {CONNECT: False},
	Will_Delay_Interval:                 {WILLPP: False}, # it is only for Will message
	Request_Response_Information:        {CONNECT: False},
	Response_Information:                {CONNACK: False},
	Server_Reference:                    {CONNACK: False, DISCONNECT: False},

	Reason_String:               { CONNACK: False, PUBACK: False, PUBREC: False, PUBREL: False, 
		                           PUBCOMP: False, SUBACK: False,  UNSUBACK: False, DISCONNECT: False, AUTH: False },

	Receive_Maximum:             {CONNECT: False, CONNACK: False},
	Topic_Alias_Maximum:         {CONNECT: False, CONNACK: False},
	Topic_Alias:                 {PUBLISH: False},
	Maximum_QoS:                 {CONNACK: False},
	Retain_Available:            {CONNACK: False},
	User_Property:               { CONNECT: True, CONNACK: True, PUBLISH: True, PUBACK: True, PUBREC: True, PUBREL: True, PUBCOMP: True,
                                   SUBSCRIBE: True, SUBACK: True, UNSUBSCRIBE: True,	UNSUBACK: True, DISCONNECT: True, AUTH: True,  WILLPP: True },

	Maximum_Packet_Size:                 {CONNECT: False, CONNACK: False},
	Wildcard_Subscription_Available:     {CONNACK: False},
	Subscription_Identifier_Available:   {CONNACK: False},
	Shared_Subscription_Available:       {CONNACK: False},
}

# Get Property data type
def property_type (ppid: int) -> int:
    return  propertyTypeMap.get(ppid, None)

# Get Property data lenght
def property_len(pptype: int, val: Any ) -> int:
    pplen = 0
    if pptype == One_Byte:
        pplen = 1
    elif pptype == Two_Byte_Integer:
        pplen = 2
    elif pptype == Four_Byte_Integer:
        pplen = 4
    elif pptype == Variable_Byte_Integer:
        pplen = vlen(val)
    elif pptype == UTF8_String:
        pplen = 2 + len(val)
    elif pptype == UTF8_String_Pair:
        pplen = 4 + len(val.k) + len(val.v)
    elif pptype == Binary_Data:
        pplen = 2 + len(val)
    return pplen


class StringPair(object):
    def __init__(self, k: str, v: str) -> None:
        self.k = k
        self.v = v


class PropertSet(object):
    def __init__(self, pktype: int) -> None:
        self.pktype = pktype
        self.props = dict()

    # reset props
    def reset(self):
        self.props = dict()

    # Set property value
    def set(self, ppid: int, v: Any) -> bool:
        if self.valid_prop(ppid):
            dup = propertyAllowedMessageTypes[ppid][self.pktype]
            if dup:
                if ppid in self.props:
                    self.props[ppid].append(v)
                else:
                    self.props[ppid] = [v]
            elif ppid in self.props[ppid]:
                # more than once
                logging.error("More than once property: %d" % ppid)
                return False
            else:
                self.props[ppid] = v
        else:
            logging.error("Invalid property id: %d." % ppid)
            return False
        return True

    # Get proerty value
    def get(self, ppid: int) -> Any:
        return self.ppros.get(ppid, None)

    # DupAllowed check if property id allows keys duplication
    def multi_allowed_property (self, ppid: int) -> bool: 
        if ppid in propertyAllowedMessageTypes:
            if self.pktype in propertyAllowedMessageTypes[ppid]:
                return propertyAllowedMessageTypes[ppid][self.pktype]
        return False

    #  Check either property id can be used for given packet type
    def valid_prop(self, ppid: int) -> bool:
        if ppid in propertyAllowedMessageTypes:
            return self.pktype in propertyAllowedMessageTypes[ppid]
        return False
    
    # read a string pair
    def read_string_pair(self, r: io.BytesIO) -> StringPair:
        k = read_string(r)
        if k is None:
            return None
        v = read_string(r)
        if v is None:
            return None
        return StringPair(k, v)

    # write a string pair
    def write_string_pair(self, w: io.BytesIO, v: StringPair) -> bool:
        len = write_string(w, v.k)
        if len==-1:
            return False
        len = write_string(w, v.v)
        if len==-1:
            return False
        return True

    # Read property value
    def read_property_val(self, r: io.BytesIO, pptype: int) -> Any:
        if pptype == One_Byte:
            v = read_int8(r)
        elif pptype == Two_Byte_Integer:
            v = read_int16(r)
        elif pptype == Four_Byte_Integer:
            v = read_int32(r)
        elif pptype == Variable_Byte_Integer:
            v = read_uvarint(r)
        elif pptype == UTF8_String:
            v = read_string(r)
        elif pptype == UTF8_String_Pair:
            v = self.read_string_pair(r)
        elif pptype == Binary_Data:
            v = read_bytes(r)
        return v

    # write a property
    def write_prop(self, w: io.BytesIO, ppid: int) -> bool:
        write_uvarint(w, ppid)
        val = self.get(ppid)
        pptype = property_type(ppid)
        if pptype == One_Byte:
            result = write_int8(w,val)
        elif pptype == Two_Byte_Integer:
            result = write_int16(w,val)
        elif pptype == Four_Byte_Integer:
            result = write_int32(w,val)
        elif pptype == Variable_Byte_Integer:
            result = write_uvarint(w, val)
        elif pptype == UTF8_String:
            result = write_string(w, val)
        elif pptype == UTF8_String_Pair:
            result = self.write_string_pair(w, val)
        elif pptype == Binary_Data:
            result = write_binary_data(w, val)
        return result

    # write multi props
    def write_multi_props(self, w: io.BytesIO, ppid: int) -> bool:
        vlist = self.get(ppid)
        if ppid == Subscription_Identifier:
            for v in vlist:
                write_uvarint(w, ppid)
                write_uvarint(w, v)
        elif ppid == User_Property:
            for v in vlist:
                self.write_string_pair(v)
        else:
            return False
        return True

    # Unpack property
    def unpack(self, r: io.BytesIO) -> bool:
        self.reset()
        pplen = read_uvarint(r)
        if pplen is None:
            logging.error("Error parsing properties lenght.")
            return False
        while pplen > 0:
            ppid = read_uvarint(r)
            if ppid is None:
                logging.error("Error parsing properties ID.")
                return False
            if not self.valid_prop(ppid):
                logging.error("Error properties ID ({}) for packet type ({})".format(ppid, self.pktype))
                return False
            pplen -= vlen(ppid)
            pptype = property_type(ppid)
            v = self.read_property_val(r)
            if v:
                if not self.set(ppid, v):
                    return False
            else:
                logging.error("Error reading property ID ({}) for packet type ({})".format(ppid, self.pktype))
                return False
            pplen -= property_len(pptype, v)
        return True

    def pack(self) -> bytes:
        w = io.BytesIO()
        for ppid in self.props:
            dup = self.multi_allowed_property(ppid)
            if dup:
                self.write_multi_props(w, ppid)
            else:
                self.write_prop(w, ppid)
        data = w.getvalue()
        w.close()
        return data

