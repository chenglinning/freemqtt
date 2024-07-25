# Copyright (C) 2020-2028, chenglinning@gmain.com
#

import json
import logging
import jwt
from tornado.web import RequestHandler

SECRETS_KEY = 'dfe042657c82fe676af9cf46f898a8033434bfbbeee37ca46e4855ad1230871d'
#APIKEY = jwt.encode({'apikey': '9766cc131fe87bc8bce04b26d2229f34'}, SECRETS_KEY, algorithm='HS256').decode()
APIKEY = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhcGlrZXkiOiI5NzY2Y2MxMzFmZTg3YmM4YmNlMDRiMjZkMjIyOWYzNCJ9.u-yGcF8BF7SEi3AnNyFwdxLGy53VF1RRK2kpJDKTryI'

error_dict = {
    0:    "suceess",
    1:    "fail",
    8000: "exception",
    8001: "not enouth input",
    9001: "not json data",
    9002: "invalid json data",
    6001: "starting",
    6002: "freemqttd has been started",
    6003: "freemqttd has been stoped",
}

class BaseHandler(RequestHandler):
    def prepare(self):
        self.set_default_header()
        self._response = {}
        self.set_error_code(0)
        self._request = {}

    def options(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        return

    def set_default_header(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def check_request_json_data(self):
        return True

    def pre_handler(self):
        remote_ip = self.request.headers.get("X-Real-IP")
        forward_ip = self.request.headers.get("X-Forwarded-For")
        logging.info(f"req_uri:{self.request.uri} remote_ip: {remote_ip}")
        if not self.content_type_is_json():
            self.set_error_code(9001)
            return False
        try:
            self._request = json.loads(self.request.body.decode('utf-8'))
            logging.info(f"request: {self._request}")
        except ValueError as e:
            self.set_error_code(9002)
            return False
        
        return self.check_request_json_data()

    async def my_handler(self):
        pass

    async def post(self):
        if self.pre_handler():
            """
            try:
                await self.my_handler()
            except Exception as e:
                logging.info('Exception: %s' % (e))
                self.set_error_code(8000)
            else:
                logging.info('res_data: %s' % (self._response))
            """
            await self.my_handler()
            logging.info('response: %s' % (self._response))
            
        self.write(json.dumps(self._response))

    def content_type_is_json(self):
        _content_type = self.request.headers.get("Content-Type")
        if _content_type and ("application/json" in _content_type.lower()):
            return True
        return False

    def set_error_code(self, code):
        self._response["error_code"] = code
        self._response["error_string"] = self.get_error_string(code)

    def set_error_string(self, message):
        self._response["error_string"] = message

    def get_error_string(self, code):
        return error_dict[code]

    def get_return_data(self):
        return self._response

    def check_json_item(self, item_key, item_type):
        if not item_key in self._request:
            self.set_error_code(8001)
            return False
        if not isinstance(self._request[item_key], item_type):
            self.set_error_code(9002)
            return False
        return True
    
    def verify_jwtoken(self):
        jwtoken = None
        userid = None
        auth = self.request.headers.get("Authorization", None)
        if auth:
            try:
                tag, jwtoken = auth.split(" ")
            except:
                jwtoken = None
            if tag != "Bearer":
                jwtoken = None
            if jwtoken:
                try:
                    jwt_data = jwt.decode(jwtoken, SECRETS_KEY, algorithms=['HS256'])
                except:
                    None
        return jwtoken
