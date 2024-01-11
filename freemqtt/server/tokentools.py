# Copyright (C) Chenglin Ning chenglinning@gmail.com
#
import hashlib
from typing import Dict
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
from Crypto.Util.Padding import unpad, pad

HEX_KEY = 'f593bde387f7530cf0f35cc2db763f75'
HEX_IV = '5ab770e779c0fd0c3ab018e7439e2a3d'

def signToken(appid:str, /) -> str:
    nonce = get_random_bytes(4).hex()
    data0 = appid+nonce
    hexHash = hashlib.md5(data0.encode('utf8')).hexdigest()[:8]
    data2 = f"{appid}:{nonce}:{hexHash}"

    key = bytes.fromhex(HEX_KEY)
    iv = bytes.fromhex(HEX_IV)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(data2.encode('utf-8'), AES.block_size))
    ct64 = b64encode(ct).decode('utf-8')
    return ct64

def verifyToken(token:str, /) -> str:
    key = bytes.fromhex(HEX_KEY)
    iv = bytes.fromhex(HEX_IV)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = b64decode(token)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    pt = pt.decode('utf8')
    appid, nonce, sig = pt.split(':')
    data0 = appid+nonce
    hexHash = hashlib.md5(data0.encode('utf8')).hexdigest()[:8]
    if sig==hexHash:
        return appid
    return None

def signToken2(appid:str, appname, /) -> str:
    nonce = get_random_bytes(4).hex()
    data0 = appid+appname+nonce
    hexHash = hashlib.md5(data0.encode('utf8')).hexdigest()[:8]
    data2 = f"{appid}:{appname}:{nonce}:{hexHash}"

    key = bytes.fromhex(HEX_KEY)
    iv = bytes.fromhex(HEX_IV)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(data2.encode('utf-8'), AES.block_size))
    ct64 = b64encode(ct).decode('utf-8')
    return ct64

def verifyToken2(token:str, /) -> str:
    key = bytes.fromhex(HEX_KEY)
    iv = bytes.fromhex(HEX_IV)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = b64decode(token)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    pt = pt.decode('utf8')
    appid, appname, nonce, sig = pt.split(':')
    data0 = appid+appname+nonce
    hexHash = hashlib.md5(data0.encode('utf8')).hexdigest()[:8]
    if sig==hexHash:
        return (appid, appname, nonce, sig)
    return None
