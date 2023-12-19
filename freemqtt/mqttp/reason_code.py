# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#

from enum import IntEnum
from .pktype import PacketType, QoS
class Reason(IntEnum):
	Success                             = 0x00
	RefusedUnacceptableProtocolVersion  = 0x01
	RefusedIdentifierRejected           = 0x02
	RefusedServerUnavailable            = 0x03
	RefusedBadUsernameOrPassword        = 0x04

	DisconnectWithWillMessage 			= 0x04

	RefusedNotAuthorized                = 0x05
	NoMatchingSubscribers               = 0x10
	NoSubscriptionExisted               = 0x11
	ContinueAuthentication              = 0x18
	ReAuthenticate                      = 0x19
	UnspecifiedError                    = 0x80
	MalformedPacket                     = 0x81
	ProtocolError                       = 0x82
	ImplementationSpecificError         = 0x83
	UnsupportedProtocol                 = 0x84
	InvalidClientID                     = 0x85
	BadUserOrPassword                   = 0x86
	NotAuthorized                       = 0x87
	ServerUnavailable                   = 0x88
	ServerBusy                          = 0x89
	Banned                              = 0x8A
	ServerShuttingDown                  = 0x8B
	BadAuthMethod                       = 0x8C
	KeepAliveTimeout                    = 0x8D
	SessionTakenOver                    = 0x8E
	InvalidTopicFilter                  = 0x8F
	InvalidTopicName                    = 0x90
	PacketIDInUse                       = 0x91
	PacketIDNotFound                    = 0x92
	ReceiveMaximumExceeded              = 0x93
	InvalidTopicAlias                   = 0x94
	PacketTooLarge                      = 0x95
	MessageRateTooHigh                  = 0x96
	QuotaExceeded                       = 0x97
	AdministrativeAction                = 0x98
	InvalidPayloadFormat                = 0x99
	RetainNotSupported                  = 0x9A
	NotSupportedQoS                     = 0x9B
	UseAnotherServer                    = 0x9C
	ServerMoved                         = 0x9D
	SharedSubscriptionNotSupported      = 0x9E
	ConnectionRateExceeded              = 0x9F
	MaximumConnectTime                  = 0xA0
	SubscriptionIDNotSupported          = 0xA1
	WildcardSubscriptionsNotSupported   = 0xA2

packetTypeReasonCodeMap = {
	PacketType.CONNACK: {
		Reason.Success:                            True,
		Reason.RefusedUnacceptableProtocolVersion: True,
		Reason.RefusedIdentifierRejected:          True,
		Reason.RefusedServerUnavailable:           True,
		Reason.RefusedBadUsernameOrPassword:       True,
		Reason.RefusedNotAuthorized:               True,
		Reason.UnspecifiedError:                   True,
		Reason.MalformedPacket:                    True,
		Reason.ImplementationSpecificError:        True,
		Reason.UnsupportedProtocol:                True,
		Reason.InvalidClientID:                    True,
		Reason.BadUserOrPassword:                  True,
		Reason.NotAuthorized:                      True,
		Reason.ServerUnavailable:                  True,
		Reason.ServerBusy:                         True,
		Reason.Banned:                             True,
		Reason.BadAuthMethod:                      True,
		Reason.InvalidTopicName:                   True,
		Reason.PacketTooLarge:                     True,
		Reason.QuotaExceeded:                      True,
		Reason.RetainNotSupported:                 True,
		Reason.NotSupportedQoS:                    True,
		Reason.UseAnotherServer:                   True,
		Reason.ServerMoved:                        True,
		Reason.ConnectionRateExceeded:             True,
	},

	PacketType.PUBACK: {
		Reason.Success:                     True,
		Reason.NoMatchingSubscribers:       True,
		Reason.UnspecifiedError:            True,
		Reason.ImplementationSpecificError: True,
		Reason.NotAuthorized:               True,
		Reason.InvalidTopicName:            True,
		Reason.QuotaExceeded:               True,
		Reason.InvalidPayloadFormat:        True,
	},

	PacketType.PUBREC: {
		Reason.Success:                     True,
		Reason.NoMatchingSubscribers:       True,
		Reason.UnspecifiedError:            True,
		Reason.ImplementationSpecificError: True,
		Reason.NotAuthorized:               True,
		Reason.InvalidTopicName:            True,
		Reason.PacketIDInUse:               True,
		Reason.QuotaExceeded:               True,
		Reason.InvalidPayloadFormat:        True,
	},

	PacketType.PUBREL: {
		Reason.Success:          True,
		Reason.PacketIDNotFound: True,
	},
	
	PacketType.PUBCOMP: {
		Reason.Success:          True,
		Reason.PacketIDNotFound: True,
	},

	PacketType.SUBACK: {
		QoS.qos0: True,
		QoS.qos1: True,
		QoS.qos2: True,
		Reason.UnspecifiedError:                  True,
		Reason.ImplementationSpecificError:       True,
		Reason.NotAuthorized:                     True,
		Reason.InvalidTopicFilter:                True,
		Reason.PacketIDInUse:                     True,
		Reason.QuotaExceeded:                     True,
		Reason.SharedSubscriptionNotSupported:    True,
		Reason.SubscriptionIDNotSupported:        True,
		Reason.WildcardSubscriptionsNotSupported: True,
	},

	PacketType.UNSUBACK: {
		Reason.Success:                     True,
		Reason.NoSubscriptionExisted:       True,
		Reason.UnspecifiedError:            True,
		Reason.ImplementationSpecificError: True,
		Reason.NotAuthorized:               True,
		Reason.InvalidTopicFilter:          True,
		Reason.PacketIDInUse:               True,
	},

	PacketType.DISCONNECT: {
		Reason.Success:                           True,
		Reason.DisconnectWithWillMessage:         True,
		Reason.UnspecifiedError:                  True,
		Reason.MalformedPacket:                   True,
		Reason.ProtocolError:                     True,
		Reason.ImplementationSpecificError:       True,
		Reason.NotAuthorized:                     True,
		Reason.ServerBusy:                        True,
		Reason.ServerShuttingDown:                True,
		Reason.KeepAliveTimeout:                  True,
		Reason.SessionTakenOver:                  True,
		Reason.InvalidTopicFilter:                True,
		Reason.InvalidTopicName:                  True,
		Reason.PacketTooLarge:                    True,
		Reason.ReceiveMaximumExceeded:            True,
		Reason.InvalidTopicAlias:                 True,
		Reason.MessageRateTooHigh:                True,
		Reason.QuotaExceeded:                     True,
		Reason.AdministrativeAction:              True,
		Reason.InvalidPayloadFormat:              True,
		Reason.RetainNotSupported:                True,
		Reason.NotSupportedQoS:                   True,
		Reason.UseAnotherServer:                  True,
		Reason.ServerMoved:                       True,
		Reason.SharedSubscriptionNotSupported:    True,
		Reason.ConnectionRateExceeded:            True,
		Reason.MaximumConnectTime:                True,
		Reason.SubscriptionIDNotSupported:        True,
		Reason.WildcardSubscriptionsNotSupported: True,
	},
	PacketType.AUTH: {
		Reason.Success: True,
		Reason.ContinueAuthentication: True,
		Reason.ReAuthenticate: True,
	},
}


def valid_reason_code3(rc: int) -> bool:
	return rc <= Reason.RefusedNotAuthorized

def valid_reason_code5(rc: int) -> bool:
	return (rc==Reason.Success or rc>=Reason.NoMatchingSubscribers) and rc <= Reason.WildcardSubscriptionsNotSupported

# IsValidForType check either reason code is valid for giver packet type
def validReasoneCode(rc: int, pktype: int) -> bool:
	if pktype in packetTypeReasonCodeMap:
		return rc in packetTypeReasonCodeMap[pktype]
	return False
