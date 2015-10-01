"""
@author: Shueng Xu   UPI: sxu487   Student ID: 8260026
"""

import sys, os, time, _thread as thread
from socket import *

blksz = 1024
defaultHost = 'localhost'
defaultPort = 8080

helptext = """
Usage...
python3 client.py download -filename xxx    --- download file xxx
python3 client.py ls                        --- list directory
"""

def now(): 
    return time.asctime()

def parsecommandline():
    dict = {}                        # put in dictionary for easy lookup
    args = sys.argv[1:]              # skip program name at front of args
    while len(args) >= 2:            # example: dict['-mode'] = 'server'
        dict[args[0]] = args[1]
        args = args[2:]
    return dict


def client(host, port, filename):
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((host, port))
    sock.send((filename + '\n').encode())      # send remote name with dir: bytes
    dropdir = os.path.split(filename)[1]       # filename at end of dir path

    print("Client filename = %s" % dropdir)

    file = open(dropdir, 'wb')                 # create local file in cwd
    while True:
        data = sock.recv(blksz)                # get up to 1K at a time
        if not data: break                     # till closed on server side
        file.write(data)                       # store data in local file
    sock.close()
    file.close()
    print('Client got', filename, 'at', now())




def main(args):
 
    if args.get("-filename"):                       # client mode needs -file
        client(defaultHost, defaultPort, args["-filename"])
    elif arg.get("ls"):
        client(defaultHost, defaultPort, "ls")
    else:
        print(helptext)

if __name__ == '__main__':
    args = parsecommandline()
    main(args)
