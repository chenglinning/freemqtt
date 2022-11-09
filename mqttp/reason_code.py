# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
from .pktype import *
QoS0 = 0
QoS1 = 1
QoS2 = 2

Success                             = 0x00
RefusedUnacceptableProtocolVersion  = 0x01
RefusedIdentifierRejected           = 0x02
RefusedServerUnavailable            = 0x03
RefusedBadUsernameOrPassword        = 0x04
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

packetTypeCodeMap = {
	CONNACK: {
		Success:                            True,
		RefusedUnacceptableProtocolVersion: True,
		RefusedIdentifierRejected:          True,
		RefusedServerUnavailable:           True,
		RefusedBadUsernameOrPassword:       True,
		RefusedNotAuthorized:               True,
		UnspecifiedError:                   True,
		MalformedPacket:                    True,
		ImplementationSpecificError:        True,
		UnsupportedProtocol:                True,
		InvalidClientID:                    True,
		BadUserOrPassword:                  True,
		NotAuthorized:                      True,
		ServerUnavailable:                  True,
		ServerBusy:                         True,
		Banned:                             True,
		BadAuthMethod:                      True,
		InvalidTopicName:                   True,
		PacketTooLarge:                     True,
		QuotaExceeded:                      True,
		RetainNotSupported:                 True,
		NotSupportedQoS:                    True,
		UseAnotherServer:                   True,
		ServerMoved:                        True,
		ConnectionRateExceeded:             True,
	},

	PUBACK: {
		Success:                     True,
		NoMatchingSubscribers:       True,
		UnspecifiedError:            True,
		ImplementationSpecificError: True,
		NotAuthorized:               True,
		InvalidTopicName:            True,
		QuotaExceeded:               True,
		InvalidPayloadFormat:        True,
	},

	PUBREC: {
		Success:                     True,
		NoMatchingSubscribers:       True,
		UnspecifiedError:            True,
		ImplementationSpecificError: True,
		NotAuthorized:               True,
		InvalidTopicName:            True,
		PacketIDInUse:               True,
		QuotaExceeded:               True,
		InvalidPayloadFormat:        True,
	},

	PUBREL: {
		Success:          True,
		PacketIDNotFound: True,
	},
	
	PUBCOMP: {
		Success:          True,
		PacketIDNotFound: True,
	},

	SUBACK: {
		QoS0:                              True,
		QoS1:                              True,
		QoS2:                              True,
		UnspecifiedError:                  True,
		ImplementationSpecificError:       True,
		NotAuthorized:                     True,
		InvalidTopicFilter:                True,
		PacketIDInUse:                     True,
		QuotaExceeded:                     True,
		SharedSubscriptionNotSupported:    True,
		SubscriptionIDNotSupported:        True,
		WildcardSubscriptionsNotSupported: True,
	},

	UNSUBACK: {
		Success:                     True,
		NoSubscriptionExisted:       True,
		UnspecifiedError:            True,
		ImplementationSpecificError: True,
		NotAuthorized:               True,
		InvalidTopicFilter:          True,
		PacketIDInUse:               True,
	},

	DISCONNECT: {
		Success:                           True,
		RefusedBadUsernameOrPassword:      True,
		UnspecifiedError:                  True,
		MalformedPacket:                   True,
		ProtocolError:                     True,
		ImplementationSpecificError:       True,
		NotAuthorized:                     True,
		ServerBusy:                        True,
		ServerShuttingDown:                True,
		KeepAliveTimeout:                  True,
		SessionTakenOver:                  True,
		InvalidTopicFilter:                True,
		InvalidTopicName:                  True,
		PacketTooLarge:                    True,
		ReceiveMaximumExceeded:            True,
		InvalidTopicAlias:                 True,
		MessageRateTooHigh:                True,
		QuotaExceeded:                     True,
		AdministrativeAction:              True,
		InvalidPayloadFormat:              True,
		RetainNotSupported:                True,
		NotSupportedQoS:                   True,
		UseAnotherServer:                  True,
		ServerMoved:                       True,
		SharedSubscriptionNotSupported:    True,
		ConnectionRateExceeded:            True,
		MaximumConnectTime:                True,
		SubscriptionIDNotSupported:        True,
		WildcardSubscriptionsNotSupported: True,
	},
	AUTH: {
		Success: True,
		ContinueAuthentication: True,
		ReAuthenticate: True,
	},
}

codeDescMap = {
	Success:                            "Operation success",
	RefusedUnacceptableProtocolVersion: "The Server does not support the level of the MQTT protocol requested by the Client",
	RefusedIdentifierRejected:          "The Client identifier is not allowed",
	RefusedServerUnavailable:           "Server refused connection",
	RefusedBadUsernameOrPassword:       "The data in the user name or password is malformed",
	RefusedNotAuthorized:               "The Client is not authorized to connect",
	NoMatchingSubscribers:              "The message is accepted but there are no subscribers",
	NoSubscriptionExisted:              "No matching subscription existed",
	ContinueAuthentication:             "Continue the authentication with another step",
	ReAuthenticate:                     "Initiate a re-authentication",
	UnspecifiedError:                   "Return code not specified by application",
	MalformedPacket:                    "Malformed Packet",
	ProtocolError:                      "Protocol Error",
	ImplementationSpecificError:        "Implementation specific error",
	UnsupportedProtocol:                "Unsupported Protocol Version",
	InvalidClientID:                    "Client Identifier not valid",
	BadUserOrPassword:                  "Bad User Name or Password",
	NotAuthorized:                      "Not authorized",
	ServerUnavailable:                  "Server unavailable",
	ServerBusy:                         "Server busy",
	Banned:                             "Banned",
	ServerShuttingDown:                 "Server shutting down",
	BadAuthMethod:                      "Bad authentication method",
	KeepAliveTimeout:                   "Keep Alive timeout",
	SessionTakenOver:                   "Session taken over",
	InvalidTopicFilter:                 "Topic Filter invalid",
	InvalidTopicName:                   "Topic Name invalid",
	PacketIDInUse:                      "Packet Identifier in use",
	PacketIDNotFound:                   "Packet Identifier not found",
	ReceiveMaximumExceeded:             "Receive Maximum exceeded",
	InvalidTopicAlias:                  "Topic Alias invalid",
	PacketTooLarge:                     "Packet too large",
	MessageRateTooHigh:                 "Message rate too high",
	QuotaExceeded:                      "Quota exceeded",
	AdministrativeAction:               "Administrative action",
	InvalidPayloadFormat:               "Payload format invalid",
	RetainNotSupported:                 "Retain not supported",
	NotSupportedQoS:                    "QoS not supported",
	UseAnotherServer:                   "Use another server",
	ServerMoved:                        "Server moved",
	SharedSubscriptionNotSupported:     "Shared Subscriptions not supported",
	ConnectionRateExceeded:             "Connection rate exceeded",
	MaximumConnectTime:                 "Maximum connect time",
	SubscriptionIDNotSupported:         "Subscription Identifiers not supported",
	WildcardSubscriptionsNotSupported:  "Wildcard Subscriptions not supported",
}

def valid_reason_code(rc: int) -> bool:
	return rc in codeDescMap

def valid_reason_code3(rc: int) -> bool:
	return rc <= RefusedNotAuthorized

def valid_reason_code5(rc: int) -> bool:
	return (rc==Success or rc>=NoMatchingSubscribers) and rc <= WildcardSubscriptionsNotSupported

# IsValidForType check either reason code is valid for giver packet type
def valid4pktype(rc: int, pktype:int) -> bool:
	if pktype in packetTypeCodeMap:
		return rc in packetTypeCodeMap[pktype]
	return False

# Desc return code description
def reason_description(rc: int) -> str:
	return codeDescMap[rc]
