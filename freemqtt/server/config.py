# Copyright (C) Chenglin Ning chenglinning@gmail.com
# All rights reserved
# Code Licenced under Apache 2.
#       http://www.apache.org/licenses/LICENSE-2.0
#
class Config:
    session_expiry_interval = 7200 # in second
    message_expiry_interval = 7200 # in second
    receive_maximum = 512
    maximum_packet_size = 2097152 # 2*1024*1024 = 2M bytes
    maximum_qos = 2
    retain_available = True
    topic_alias_maximum = 64
    wildcard_subscription_available = True
    subscription_identifiers_available = True
    shared_subscription_available = True
    server_keep_alive = 60 # in second
    response_information = "Welcome to FreeMQTT Broker."
    maximun_connection = 32