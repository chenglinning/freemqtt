# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import io
import logging
import struct
import re

# TopicFilterRegexp regular expression that all subscriptions must be validated
TopicFilterRegexp = re.compile(r'^(([^+#]*|\+)(/([^+#]*|\+))*(/#)?|#)$')
# TopicPublishRegexp regular expression that all publish to topic must be validated
TopicPublishRegexp = re.compile(r'^[^#+]*$')
# SharedTopicRegexp regular expression that all share subscription must be validated
SharedTopicRegexp = re.compile(r'^\$share/([^#+/]+)(/)(.+)$')
# BasicUTFRegexp regular expression all MQTT strings must meet [MQTT-1.5.3]
BasicUTFRegexp = re.compile(r'^[^\u0000-\u001F\u007F-\u009F]*$')

def vlen (u: int) ->int:
	if u < 128:
		return 1
	if u < 16384:
		return 2
	if u < 2097152:
		return 3
	if u < 268435456:
		return 4
	return 0

def read_int8(r: io.BytesIO) -> int:
    buff = r.read(1)
    if buff:
        v, = struct.unpack("!B", buff)
    else:
        v = -1
    return v

def write_int8(w: io.BytesIO, v: int) -> int:
    return w.write(struct.pack("!B", v))

def read_int16(r: io.BytesIO) -> int:
    buff = r.read(2)
    if len(buff)==2:
        v, = struct.unpack("!H", buff)
    else:
        v = -1
    return v

def write_int16(w: io.BytesIO, v: int) -> int:
    return w.write(struct.pack("!H", v))

def read_int32(r: io.BytesIO) -> int:
    buff = r.read(4)
    if len(buff)==4:
        v, = struct.unpack("!I", buff)
    else:
        v = -1
    return v

def write_int32(w: io.BytesIO, v: int) -> int:
    return w.write(struct.pack("!I", v))
 

def read_string(r: io.BytesIO) -> str:
    rlen = read_int16(r)
    if rlen < 0:
        return None
    if rlen==0:
        return ""
    try:
        utf8str = r.read(rlen)
        v = utf8str.decode("utf8")
        if not BasicUTFRegexp.match(v):
            logging.error("Invalid UTF8 string.")
            v = None
    except Exception as e:
        logging.exception(repr(e))
        v = None
    return v

def write_string(w: io.BytesIO, v: str) -> int:
    rlen = -1
    if not BasicUTFRegexp.match(v):
        logging.error("Invalid UTF8 string.")
        return -1
    try:
        utf8s = v.encode("utf-8")
        rlen = len(utf8s)
        w.write(struct.pack("!H", rlen))
        w.write(utf8s)
    except Exception as e:
        logging.exception(repr(e))
    return rlen

def read_uvarint(r: io.BytesIO) -> int:
    val = 0; mtp = 1
    while True:
        buff = r.read(1)
        if buff:
            b, = struct.unpack("!B", buff)
            val += (b & 0x7F) * mtp
            mtp *= 128
            if mtp > 2097152: # 128*128*128 = 2^21
                return None
            if not (b & 0x80):
                break
        elif mtp==1:
            return 0
        else:
            return None
    return val

def write_uvarint(w: io.BytesIO, v: int) -> bool:
    if v > 268435455:
        return False
    X = v
    while True:
        b = X % 128
        X =  X // 128
        # If there are more digits to encode, set the top bit of this digit
        if X > 0:
            b |= 0x80
        w.write(struct.pack("!B", b))
        if X == 0:
            break
    return True

def read_binary_data(r: io.BytesIO) -> bytes:
    len = read_int16(r)
    if len is None:
        return None
    return r.read(len)

def write_binary_data(w: io.BytesIO, v: bytes) -> int:
    write_int16(w, len(v))
    return w.write(v)

def read_rest_data(r: io.BytesIO) -> bytes:
    return r.read()

def read_bytes(r: io.BytesIO) -> bytes:
    return r.read()

def write_bytes(w: io.BytesIO, v: bytes) -> int:
    return w.write(v)
