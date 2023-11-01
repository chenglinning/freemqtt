# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
Type    = 0xF0
Flags   = 0x0F
Qos     = 0x06
Dup     = 0x08
Retain  = 0x01

MessageFlags                = 0x0F
ConnFlagUsername            = 0x80
ConnFlagPassword            = 0x40
ConnFlagWillRetain          = 0x20
ConnFlagWillQos             = 0x18
ConnFlagWill                = 0x04
ConnFlagClean               = 0x02
ConnFlagReserved            = 0x01
PublishFlagRetain           = 0x01
PublishFlagQoS              = 0x06
PublishFlagDup              = 0x08
SubscriptionQoS             = 0x03
SubscriptionNL              = 0x04
SubscriptionRAP             = 0x08
SubscriptionRetainHandling  = 0x30
SubscriptionReservedV3      = 0xFC
SubscriptionReservedV5      = 0xC0
SessionPresent              = 0x01
