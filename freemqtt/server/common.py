# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#

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


# connection state
class State(IntEnum):
    INITIATED       = 0
    CONNECTING      = 1
    CONNECTED       = 2    
    DISCONNECTING   = 3
    DISCONNECTED    = 4
    KICKOUT         = 5
    CLOSING_FOR_EXCEPTION = 6
    CLOSING          = 7
    CLOSED          = 8

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
