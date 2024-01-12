import uuid
from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken, verifyToken
appid = uuid.uuid1().hex[0:8]
#appname = 'demo'
appname = '家悦'
if __name__ == "__main__":
    app = f'{appid}@{appname}'
    token = signToken(app)
    data = verifyToken(token)
    print ("******************************")
    print (token)
    print (data)
    print ("===============================")

# for guojie_app 
# hx5hMRJ8z+5guo7qh6RNZPsw3quEOT+n50lyGCZg09A=
        
# demo
# wNMAP5SRt53QkEf47mLrbBVDqcRtiuHlLAUMQxSPG1E=