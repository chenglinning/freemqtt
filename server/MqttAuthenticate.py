# -*- coding: utf-8 -*-
#
# Copyright (C) 2010-2014 Internet Message Shuttle
# Chenglin Ning, chenglinning@gmail.com
#
# All rights reserved
#
#
import json
import jwt
import logging

from ..core.MqttException import MqttException
SECRETS_KEY = 'dfe042657c82fe676af9cf46f898a8033434bfbbeee37ca46e4855ad1230871d'

class MqttAuthenticate(object):
    
    def __init__(self):
        self.apptype = 'zwavegw'
        self.clientid = None

    def auth(self, client_id, user_id=None, password=None):
        self.clientid = client_id
        logging.info('Password: {}'.format(password))
        ret_code = MqttException.REASON_CODE_FAILED_AUTHENTICATION

        try:
            jwt_data = jwt.decode(password, SECRETS_KEY, algorithms='HS256')
        except:
            ret_code = MqttException.REASON_CODE_FAILED_AUTHENTICATION
            logging.info("jwtoken decode exception")
            return ret_code

        try:
            self.apptype = jwt_data["apptype"]
            sign_clientid = jwt_data['clientid']
            if client_id == sign_clientid:
                ret_code = MqttException.REASON_CODE_CLIENT_ACCEPTED
        except:
            logging.info("jwt_data: {} ".format(jwt_data))
            ret_code = MqttException.REASON_CODE_FAILED_AUTHENTICATION
            return ret_code

        logging.info("client_id: {} sign_clientid: {}".format(client_id, sign_clientid))

        return ret_code
    

    def verify_client_id(self, client_id):
        return True

    def verify_user_password(self, user_id, password):
        return True

    def pub_acl_list(self, client_id):
        acl = [ "{}/{}/#".format(self.apptype, client_id) ] 
        if client_id in ['skiotapi', 'monitor_admin', 'system_admin']:
            acl =  ["+/#"]
        return acl

    def sub_acl_list(self, client_id):
        # to implement your get acl list code at here
        acl = [ "{}/{}/#".format(self.apptype, client_id) ] 
        if client_id in ['skiotapi', 'monitor_admin', 'system_admin']:
            acl =  ["+/#"]

        return acl
