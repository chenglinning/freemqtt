from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken2, verifyToken2
appid = '80abcdfe'
appname='MqttBridge'
if __name__ == "__main__":
    token = signToken2(appid, appname)
    data = verifyToken2(token)
    print ("******************************")
    print (token)
    print (data)

# for guojie_app 
# hx5hMRJ8z+5guo7qh6RNZPsw3quEOT+n50lyGCZg09A=
        
# demo
# wNMAP5SRt53QkEf47mLrbBVDqcRtiuHlLAUMQxSPG1E=