from server.tokentools import signToken, verifyToken
if __name__ == "__main__":
    token = signToken("12abcdefedeee")
    data = verifyToken(token)
    print (token)
    print (data)
