# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import re
from typing import NewType
from enum import IntEnum

from ..mqttp.pktype import PacketType
from ..mqttp.connect import Connect
from ..mqttp.connack import Connack
from ..mqttp.publish import Publish
from ..mqttp.puback import Puback
from ..mqttp.pubrec import Pubrec
from ..mqttp.pubrel import Pubrel
from ..mqttp.pubcomp import Pubcomp
from ..mqttp.subscribe import Subscribe
from ..mqttp.suback import Suback
from ..mqttp.unsubscribe import Unsubscribe
from ..mqttp.unsuback import Unsuback
from ..mqttp.pingreq import Pingreq
from ..mqttp.pingresp import Pingresp
from ..mqttp.disconnect import Disconnect
from ..mqttp.auth import Auth
from ..mqttp import mask


TopicFilter = NewType("TopicFilter", str)
Topic = NewType("Topic", str)
PacketID = NewType("PacketID", int)
TopicAlias = NewType("TopicAlias", int)
ClientID = NewType("ClientID", str)
AppID = NewType("AppID", str)
ShareName = NewType("ShareName", str)
NodeID = NewType("NodeID", str)

TopicFilterRegexp = re.compile(r'^[^/](([^+#]*|\+)(/([^+#]*|\+))*(/#)?|#)$')
TopicPublishRegexp = re.compile(r'^[^/$][^#+]*$')
SharedTopicRegexp = re.compile(r'^\$share/([^#+/]+)(/)(.+)$')
BasicUTFRegexp = re.compile(r'^[^\u0000-\u001F\u007F-\u009F]*$')
FACTOR = 1.382

# connection state
class State(IntEnum):
    INITIATED       = 0
    CONNECTING      = 1
    CONNECTED       = 2    
    DISCONNECTED_BY_CLIENT   = 3
    DISCONNECTED_BY_SERVER   = 4
    KICKOUT         = 5
    CLOSING_FOR_EXCEPTION = 6
    CLOSED4TIMEOUT  = 7
    CLOSED          = 8
    WAITING_EXPIRED = 9
    EXPIRED         = 10

# packet class map
PacketClass = {
    PacketType.CONNECT:     Connect,
    PacketType.CONNACK:     Connack,
    PacketType.PUBLISH:     Publish,
    PacketType.PUBACK:      Puback,
    PacketType.PUBREC:      Pubrec,
    PacketType.PUBREL:      Pubrel,
    PacketType.PUBCOMP:     Pubcomp,
    PacketType.SUBSCRIBE:   Subscribe,
    PacketType.SUBACK:      Suback,
    PacketType.UNSUBSCRIBE: Unsubscribe,
    PacketType.UNSUBACK:    Unsuback,
    PacketType.PINGREQ:     Pingreq,
    PacketType.PINGRESP:    Pingresp,
    PacketType.DISCONNECT:  Disconnect,
    PacketType.AUTH:        Auth,
}

class SubOption(object):
    def __init__(self, options:int=0, subid: int=None) -> None:
        self.options = options
        self.subid = subid

    def SubscriptionID(self) -> int:
        return self.subid
    
    def QoS(self) -> int:
        return self.options & mask.SubscriptionQoS

    def NL(self) -> bool:
        return self.options & mask.SubscriptionNL != 0
    
    def RAP(self) -> bool:
        return self.options & mask.SubscriptionRAP != 0

    def RH(self) -> int:
        return self.options & mask.SubscriptionRetainHandling >> 4

    def setQoS(self, qos: int) -> None:
        self.options =  (self.options & ~mask.SubscriptionQoS) | qos
        
    def setNL(self, nl:bool) -> None:
        self.options = (self.options & ~mask.SubscriptionNL) | (nl << 2)

    def setRAP(self, rap: bool) -> None:
        self.options = (self.options & ~mask.SubscriptionRAP) | (rap << 3)

    def setRH(self, rh: int) -> None:
        self.options = (self.options & ~mask.SubscriptionRetainHandling) | (rh <<4)
