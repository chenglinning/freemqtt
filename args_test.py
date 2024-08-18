import sys
import uuid
import argparse
appid = uuid.uuid1().hex[0:8]
if __name__ == "__main__":
    if "args_test.py"in sys.argv[0] :
        print ("*** python", sys.argv[0])
    else:
        print (sys.argv[0])

    print(appid)
    parser = argparse.ArgumentParser()
    parser.add_argument("command", help="start | stop | status | restart", choices=["start", "stop", "status", "restart"])
    args = parser.parse_args()
    print("***", args)


