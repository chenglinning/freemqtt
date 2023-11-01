# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import json
import jwt
import logging
from typing import Tuple, List
from ..mqttp import reason_code as ReasonCode

SECRETS_KEY = 'dfe042657c82fe676af9cf46f898a8033434bfbbeee37ca46e4855ad1230871d'

class AuthPlugin(object):
    def __init__(self):
        self.username = None
        self.appid = None
        self.appname = None

    def auth_token(self, token:str=None) -> Tuple:
        logging.info(f'token: {token}')
        ret_code = ReasonCode.Success
        try:
            jwt_data = jwt.decode(token, SECRETS_KEY, algorithms=['HS256'])
        except:
            ret_code = ReasonCode.RefusedBadUsernameOrPassword
            logging.info("jwtoken decode exception")
            return (ret_code, None, None, None)

        try:
            self.username = jwt_data["username"]
            self.appid = jwt_data["appid"]
            self.appname = jwt_data["appname"]
            nonce = jwt_data["nonce"]
        except:
            logging.info("jwt_data: {} ".format(jwt_data))
            ret_code = ReasonCode.RefusedBadUsernameOrPassword
            return (ret_code, None, None, None)

        logging.info(f"Auth appid: {self.appid} appname: {self.appname}  username: {self.username} nonce: {nonce}")

        return (ret_code, self.username, self.appid, self.appname)
    
    def pub_acl_list(self) -> List:
        acl = ["#"] 
        return acl
        
    def sub_acl_list(self, client_id):
        # to implement your get acl list code at here
        acl = ["#"] 
        return acl
