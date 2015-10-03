#!/usr/bin/env python
# coding: utf-8

import sys, posix, string
from socket import *

HOSTNAME = "127.0.0.1"
BUFSIZE = 1024

# Default port numbers used by the FTP protocol.
#
#FTP_PORT = 8888  # connect to real server
FTP_PORT = 3333  # connect to cache server
FTP_DATA_PORT = FTP_PORT - 1

# Change the data port to something not needing root permissions.
#
FTP_DATA_PORT = FTP_DATA_PORT + 50000

FILENAME = ""

# Main program (called at the end of this file).
#
def main():
    hostname = HOSTNAME
    control(hostname)


# Control process (user interface and user protocol interpreter).
#
def control(hostname):
    #
    # Create control connection
    #
    global FILENAME
    s = socket(AF_INET, SOCK_STREAM)
    s.connect((hostname, FTP_PORT))
    f = s.makefile('r') # Reading the replies is easier from a file...
    #
    # Control loop
    #
    r = None
    while 1:
        code = getreply(f)
        if code in ('221', 'EOF'):
            break
        if code == '150':
            getdata(r)
            code = getreply(f)
            r = None
        if not r:
            r = newdataport(s, f)
        cmd = getcommand()
        if not cmd: 
            break

        s.send(cmd + "\r\n")
        if cmd.find("retr") != -1:
            FILENAME = cmd[5:]
    

# Create a new data port and send a PORT command to the server for it.
# (Cycle through a number of ports to avoid problems with reusing
# a port within a short time.)
#
nextport = 0
#
def newdataport(s, f):
    global nextport
    port = nextport + FTP_DATA_PORT
    nextport = (nextport+1) % 16
    r = socket(AF_INET, SOCK_STREAM)
    r.bind((HOSTNAME, port))
    r.listen(1)
    sendportcmd(s, f, port)
    return r


# Send an appropriate port command.
#
def sendportcmd(s, f, port):
    hostaddr = HOSTNAME
    hbytes = string.splitfields(hostaddr, '.')
    pbytes = [repr(port//256), repr(port%256)]
    bytes = hbytes + pbytes
    cmd = 'PORT ' + string.joinfields(bytes, ',')
    s.send(cmd + '\r\n')
    code = getreply(f)


# Process an ftp reply and return the 3-digit reply code (as a string).
# The reply should be a line of text starting with a 3-digit number.
# If the 4th char is '-', it is a multi-line reply and is
# terminate by a line starting with the same 3-digit number.
# Any text while receiving the reply is echoed to the file.
#
def getreply(f):
    line = f.readline()
    if not line: 
        return 'EOF'

    print("line = %s" % line)
    code = line[:3]
    if line[3:4] == '-':
        while 1:
            line = f.readline()
            if not line: 
                break # Really an error
            print ("line = %s" % line)
            if line[:3] == code and line[3:4] != '-': break

    return code




# Get the data from the data connection.
#
def getdata(r):
    global FILENAME

    print ('accepting data connection')
    conn, host = r.accept()
    print ('data connection accepted')
    if FILENAME == "":
        while True:
            data = conn.recv(BUFSIZE)
            if not data: 
                break
            sys.stdout.write(data)

    else:
        savefilename = "./downloads" + "/" + FILENAME
        file = open(savefilename, 'wb')                 # create local file in cwd
        while True:
            data = conn.recv(BUFSIZE)
            if not data:
                 break
            file.write(data)

        FILENAME = ""
        
    print ('end of data connection')

# Get a command from the user.
#
def getcommand():
    try:
        while 1:
            line = raw_input('client> ')
            if line: 
                return line
    except EOFError:
        return ''


# Call the main program.
#
if __name__ == "__main__":
    main()