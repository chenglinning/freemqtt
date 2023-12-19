# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
import logging
from .tokentools import verifyToken
class AuthPlugin(object):
    def __init__(self):
        self.appid = None
        self.connect_max = 128

    def auth_token(self, token:str=None) -> tuple[str, int]:
        logging.info(f'Token: {token}')
        try:
            appid = verifyToken(token)
        except Exception as e:
            logging.error(f"{e}")
            appid = None
        self.appid = appid
        logging.info(f"AppID: {appid}")
        return (self.appid, self.connect_max)
