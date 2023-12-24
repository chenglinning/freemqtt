from base64 import b64encode, b64decode
from freemqtt.server.tokentools import signToken, verifyToken
if __name__ == "__main__":
    token = signToken("guojie_app")
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
