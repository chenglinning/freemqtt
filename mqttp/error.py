# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
Success = 0
InvalidUnSubscribe = 1
InvalidUnSubAck = 2
DupViolation = 3
PackedIDNotMatched = 4
Invalid = 5
PackedIDZero = 6
OnPublishNil = 7
InvalidMessageType = 8
InvalidMessageTypeFlags = 9
InvalidQoS = 10
InvalidLength = 11
ProtocolViolation = 12
InsufficientBufferSize = 13
InsufficientDataSize = 14
InvalidTopic = 15
EmptyPayload = 16
InvalidReturnCode = 17
Unimplemented = 18
InvalidLPStringSize = 19
MalformedTopic = 20
MalformedStream = 21
InvalidProtocolVersion = 22
NotSet = 23
PanicDetected = 24
InvalidArgs = 25
InvalidUtf8 = 26
NotSupported = 27
InvalidProtocolName = 28

ErrorName = {
	Success:				"Success",
	InvalidUnSubscribe:     "Invalid UNSUBSCRIBE message",
	InvalidUnSubAck:        "Invalid UNSUBACK message",
	DupViolation:           "Duplicate violation",
	PackedIDNotMatched:     "Packet ID does not match",
	PackedIDZero:           "Packet ID cannot be 0",
	OnPublishNil:		    "Publisher is nil",
	InvalidMessageType:     "Invalid message type",
	InvalidMessageTypeFlags:"Invalid message flags",
	InvalidQoS:		        "Invalid message QoS",
	InvalidLength: 		    "Invalid message length",
	ProtocolViolation:      "Protocol violation",
	InsufficientBufferSize: "Insufficient buffer size",
	InsufficientDataSize:   "Insufficient data size",
	InvalidTopic: 		    "Invalid topic name",
	EmptyPayload:           "Payload is empty",
	InvalidReturnCode:      "Invalid return code",
	Unimplemented: 		    "Function not implemented yet",
	InvalidLPStringSize:    "Invalid LP string size",
	MalformedTopic: 		"Malformed topic",
	MalformedStream: 		"Malformed stream",
	InvalidArgs: 		    "Invalid arguments",
	InvalidUtf8:            "String is not UTF8",
	InvalidProtocolName:	"Invalid protocol name",
	InvalidProtocolVersion: "Invalid protocol level",
}

def error_desc(e: int) -> str:
    return ErrorName.get(e, None)
