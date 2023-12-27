from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken, verifyToken
appid = 'demo'
if __name__ == "__main__":
    token = signToken(appid)
    data = verifyToken(token)
    print ("******************************")
    print (token)
    print (data)
    print ("===============================")
    bs = b"mybesd"
    bs64 = b64encode(bs).decode('utf8')
    print (bs64)
    try:
        data = verifyToken(bs64)
    except Exception as e:
        print(e)

# for guojie_app 
# hx5hMRJ8z+5guo7qh6RNZPsw3quEOT+n50lyGCZg09A=
        
# demo
# wNMAP5SRt53QkEf47mLrbBVDqcRtiuHlLAUMQxSPG1E=