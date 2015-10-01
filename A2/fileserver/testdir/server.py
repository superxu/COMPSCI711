"""
@author: Shueng Xu   UPI: sxu487   Student ID: 8260026
"""
import sys, os, time, _thread as thread
from socket import *

blksz = 1024
defaultHost = 'localhost'
defaultPort = 8080


def now(): 
    return time.asctime()


def parsecommandline():
    dict = {}                        # put in dictionary for easy lookup
    args = sys.argv[1:]              # skip program name at front of args
    while len(args) >= 2:            # example: dict['-mode'] = 'server'
        dict[args[0]] = args[1]
        args = args[2:]
    return dict


def serverthread(clientsock):
    sockfile = clientsock.makefile('r')        # wrap socket in dup file obj
    filename = sockfile.readline()[:-1]        # get filename up to end-line

    print("Server filename = %s" % filename)
    if filename == "ls":
        do_get()

    try:
        file = open(filename, 'rb')
        while True:
            bytes = file.read(blksz)           # read/send 1K at a time
            if not bytes: break                # until file totally sent
            sent = clientsock.send(bytes)
            assert sent == len(bytes)
    except:
        print('Error downloading file on server:', filename)
    clientsock.close()

def server(host, port):
    serversock = socket(AF_INET, SOCK_STREAM)     # listen on TCP/IP socket
    serversock.bind((host, port))                 # serve clients in threads
    serversock.listen(5)
    while True:
        clientsock, clientaddr = serversock.accept()
        print('Server connected by', clientaddr, 'at', now())
        thread.start_new_thread(serverthread, (clientsock,))

def main(args):

    server(defaultHost, defaultPort)


if __name__ == '__main__':
    args = parsecommandline()
    main(args)

