# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging

from typing import Dict
from enum import IntEnum
from typing import Any
from .utils import * 
from .pktype import PacketType

class PropertyType(IntEnum):
    One_Byte = 0
    Two_Byte_Integer = 1
    Four_Byte_Integer = 2
    Variable_Byte_Integer = 3
    UTF8_String = 4
    UTF8_String_Pair = 5
    Binary_Data = 6
class Property(IntEnum):
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
    Property.Payload_Format_Indicator:			PropertyType.One_Byte,
    Property.Message_Expiry_Interval:           PropertyType.Four_Byte_Integer,
    Property.Content_Type:                    	PropertyType.UTF8_String,
    Property.Response_Topic:                  	PropertyType.UTF8_String,
    Property.Correlation_Data:                	PropertyType.Binary_Data,
    Property.Subscription_Identifier:         	PropertyType.Variable_Byte_Integer,
    Property.Session_Expiry_Interval:		    PropertyType.Four_Byte_Integer,
    Property.Assigned_Client_Identifier:        PropertyType.UTF8_String,
    Property.Server_Keep_Alive:                 PropertyType.Two_Byte_Integer,
    Property.Authentication_Method:             PropertyType.UTF8_String,
    Property.Authentication_Data:               PropertyType.Binary_Data,
    Property.Request_Problem_Information:       PropertyType.One_Byte,
    Property.Will_Delay_Interval:               PropertyType.Four_Byte_Integer,
    Property.Request_Response_Information:      PropertyType.One_Byte,
    Property.Response_Information:              PropertyType.UTF8_String,
    Property.Server_Reference:                  PropertyType.UTF8_String,
    Property.Reason_String:                     PropertyType.UTF8_String,
    Property.Receive_Maximum:                   PropertyType.Two_Byte_Integer,
    Property.Topic_Alias_Maximum:               PropertyType.Two_Byte_Integer,
    Property.Topic_Alias:                       PropertyType.Two_Byte_Integer,
    Property.Maximum_QoS:                       PropertyType.One_Byte,
    Property.Retain_Available:                  PropertyType.One_Byte,
    Property.User_Property:                     PropertyType.UTF8_String_Pair,
    Property.Maximum_Packet_Size:               PropertyType.Four_Byte_Integer,
    Property.Wildcard_Subscription_Available:   PropertyType.One_Byte,
    Property.Subscription_Identifier_Available: PropertyType.One_Byte,
    Property.Shared_Subscription_Available:     PropertyType.One_Byte,
}

# propertyAllowedMessageTypes properties and their supported packets type.
# bool flag indicates either duplicate allowed or not
propertyAllowedMessageTypes = {
	Property.Payload_Format_Indicator:            {PacketType.PUBLISH: False, PacketType.WILLPP: False},
	Property.Message_Expiry_Interval:             {PacketType.PUBLISH: False, PacketType.WILLPP: False},
	Property.Content_Type:                        {PacketType.PUBLISH: False, PacketType.WILLPP: False},
	Property.Response_Topic:                      {PacketType.PUBLISH: False, PacketType.WILLPP: False},
	Property.Correlation_Data:                    {PacketType.PUBLISH: False, PacketType.WILLPP: False},
	Property.Subscription_Identifier:             {PacketType.PUBLISH: True, PacketType.SUBSCRIBE: False},
	Property.Session_Expiry_Interval:             {PacketType.CONNECT: False, PacketType.CONNACK: False, PacketType.DISCONNECT: False},
	Property.Assigned_Client_Identifier:          {PacketType.CONNACK: False},
	Property.Server_Keep_Alive:                   {PacketType.CONNACK: False},
	Property.Authentication_Method:               {PacketType.CONNECT: False, PacketType.CONNACK: False, PacketType.AUTH: False},
	Property.Authentication_Data:                 {PacketType.CONNECT: False, PacketType.CONNACK: False, PacketType.AUTH: False},
	Property.Request_Problem_Information:         {PacketType.CONNECT: False},
	Property.Will_Delay_Interval:                 {PacketType.WILLPP: False}, # it is only for Will message
	Property.Request_Response_Information:        {PacketType.CONNECT: False},
	Property.Response_Information:                {PacketType.CONNACK: False},
	Property.Server_Reference:                    {PacketType.CONNACK: False, PacketType.DISCONNECT: False},

	Property.Reason_String:      { PacketType.CONNACK: False, PacketType.PUBACK: False,  PacketType.PUBREC: False, 
                                   PacketType.PUBREL: False,  PacketType.PUBCOMP: False, PacketType.SUBACK: False,  
                                   PacketType.UNSUBACK: False, PacketType.DISCONNECT: False, PacketType.AUTH: False 
                                 },

	Property.Receive_Maximum:      {PacketType.CONNECT: False, PacketType.CONNACK: False},
	Property.Topic_Alias_Maximum:  {PacketType.CONNECT: False, PacketType.CONNACK: False},
	Property.Topic_Alias:          {PacketType.PUBLISH: False},
	Property.Maximum_QoS:          {PacketType.CONNACK: False},
	Property.Retain_Available:     {PacketType.CONNACK: False},

	Property.User_Property:        { PacketType.CONNECT: True, PacketType.CONNACK: True, PacketType.PUBLISH: True, PacketType.PUBACK: True,
                                     PacketType.PUBREC: True, PacketType.PUBREL: True, PacketType.PUBCOMP: True, PacketType.SUBSCRIBE: True, 
                                     PacketType.SUBACK: True, PacketType.UNSUBSCRIBE: True,	PacketType.UNSUBACK: True, PacketType.DISCONNECT: True,
                                     PacketType.AUTH: True,  PacketType.WILLPP: True
                                   },

	Property.Maximum_Packet_Size:                 {PacketType.CONNECT: False, PacketType.CONNACK: False},
	Property.Wildcard_Subscription_Available:     {PacketType.CONNACK: False},
	Property.Subscription_Identifier_Available:   {PacketType.CONNACK: False},
	Property.Shared_Subscription_Available:       {PacketType.CONNACK: False},
}

# Get Property data type
def property_type (ppid: Property) -> PropertyType:
    return  propertyTypeMap.get(ppid, None)

# Get Property data lenght
def property_len(pptype: PropertyType, val: Any ) -> int:
    pplen = 0
    if pptype == PropertyType.One_Byte:
        pplen = 1
    elif pptype == PropertyType.Two_Byte_Integer:
        pplen = 2
    elif pptype == PropertyType.Four_Byte_Integer:
        pplen = 4
    elif pptype == PropertyType.Variable_Byte_Integer:
        pplen = vlen(val)
    elif pptype == PropertyType.UTF8_String:
        pplen = 2 + len(val)
    elif pptype == PropertyType.UTF8_String_Pair:
        pplen = 4 + len(val.k) + len(val.v)
    elif pptype == PropertyType.Binary_Data:
        pplen = 2 + len(val)
    return pplen


class StringPair(object):
    def __init__(self, k: str, v: str) -> None:
        self.k = k
        self.v = v


class PropertSet(object):
    def __init__(self, pktype: PacketType) -> None:
        self.pktype = pktype
        self.props: Dict[Property, Any] = dict()

    # reset props
    def reset(self):
        self.props = dict()

    # Set property value
    def set(self, ppid: Property, v: Any) -> bool:
        if self.valid_prop(ppid):
            dup = propertyAllowedMessageTypes[ppid][self.pktype]
            if dup:
                if ppid in self.props:
                    self.props[ppid].append(v)
                else:
                    self.props[ppid] = [v]
            else:
                self.props[ppid] = v
        else:
            logging.error(f"Invalid property {ppid.name} for {self.pktype.name}")
            return False
        return True

    # Get proerty value
    def get(self, ppid: Property) -> Any:
        return self.props.get(ppid, None)
    
    # delete proerty value
    def delete(self, ppid: Property) -> Any:
        return self.props.pop(ppid, None)

    # DupAllowed check if property id allows keys duplication
    def multi_allowed_property (self, ppid: Property) -> bool: 
        if ppid in propertyAllowedMessageTypes:
            if self.pktype in propertyAllowedMessageTypes[ppid]:
                return propertyAllowedMessageTypes[ppid][self.pktype]
        return False

    #  Check either property id can be used for given packet type
    def valid_prop(self, ppid: Property) -> bool:
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
    def write_string_pair(self, w: io.BytesIO, sp: StringPair) -> bool:
        len = write_string(w, sp.k)
        if len==-1:
            return False
        len = write_string(w, sp.v)
        if len==-1:
            return False
        return True

    # Read property value
    def read_property_val(self, r: io.BytesIO, pptype: PropertyType) -> Any:
        if pptype == PropertyType.One_Byte:
            v = read_int8(r)
        elif pptype == PropertyType.Two_Byte_Integer:
            v = read_int16(r)
        elif pptype == PropertyType.Four_Byte_Integer:
            v = read_int32(r)
        elif pptype == PropertyType.Variable_Byte_Integer:
            v = read_uvarint(r)
        elif pptype == PropertyType.UTF8_String:
            v = read_string(r)
        elif pptype == PropertyType.UTF8_String_Pair:
            v = self.read_string_pair(r)
        elif pptype == PropertyType.Binary_Data:
            v = read_binary_data(r)
        return v

    # write a property
    def write_prop(self, w: io.BytesIO, ppid: Property) -> bool:
        write_uvarint(w, ppid)
        val = self.get(ppid)
        assert(not val is None)
        logging.debug(f'O {ppid.name}: {val}')
        pptype = property_type(ppid)
        if pptype == PropertyType.One_Byte:
            result = write_int8(w,val)
        elif pptype == PropertyType.Two_Byte_Integer:
            result = write_int16(w,val)
        elif pptype == PropertyType.Four_Byte_Integer:
            result = write_int32(w,val)
        elif pptype == PropertyType.Variable_Byte_Integer:
            result = write_uvarint(w, val)
        elif pptype == PropertyType.UTF8_String:
            result = write_string(w, val)
        elif pptype == PropertyType.UTF8_String_Pair:
            result = self.write_string_pair(w, val)
        elif pptype == PropertyType.Binary_Data:
            result = write_binary_data(w, val)
        return result

    # write multi props
    def write_multi_props(self, w: io.BytesIO, ppid: Property) -> bool:
        vlist = self.get(ppid)
        if ppid == Property.Subscription_Identifier:
            for v in vlist:
                write_uvarint(w, ppid)
                write_uvarint(w, v)
                logging.debug(f'O {ppid.name}: {v}')
        elif ppid == Property.User_Property:
            for sp in vlist:
                write_uvarint(w, ppid)
                self.write_string_pair(w, sp)
                logging.debug(f'O {ppid.name}: ({sp.k}: {sp.v})')
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
            ippid = read_uvarint(r)
            if ippid is None:
                logging.error("Error parsing properties ID.")
                return False
            if not self.valid_prop(ippid):
                logging.error(f"Error properties ID ({ippid:02X}) for {self.pktype.name}")
                return False
            ppid = Property(ippid)
            pplen -= vlen(ippid)
            pptype = property_type(ippid)
            v = self.read_property_val(r, pptype)
            dup = self.multi_allowed_property(ppid)
            if not dup and ppid in self.props:
                logging.error(f'include the {ppid.name} more than once in {self.pktype.name}')
                return False
            if not self.set(ppid, v):
                return False

            if ppid==Property.User_Property:
                logging.debug(f'I {ppid.name}: ({v.k}: {v.v})')
            else:
                logging.debug(f'I {ppid.name}: {v}')
            pplen -= property_len(pptype, v)
        return True

    def pack(self) -> bytes:
       #logging.info(f'properties packing....')
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
    