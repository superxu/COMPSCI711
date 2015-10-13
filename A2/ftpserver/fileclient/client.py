#!/usr/bin/env python
# coding: utf-8

import sys, posix, string
from socket import *
from form import Form 
from Tkinter import Tk, mainloop
import os, thread 
import tkMessageBox

HOSTNAME = "127.0.0.1"
BUFSIZE = 1024



FILENAME = ""


class FtpForm(Form):
    def __init__(self):
        root = Tk()
        root.title(self.title)
        root.geometry("600x600")
        labels = ['Server Name', 'Port Number']
        Form.__init__(self, labels)
        self.mutex = thread.allocate_lock()
        self.threads = 0
        self.portnum = 0
        self.nextport = 0
        self.servername = ""
        self.filename = ""
        self.socket = None
    

    def transfer(self, filename, servername, remotedir, userinfo):
        try:
            self.do_transfer(filename, servername, remotedir, userinfo)
            print('%s of "%s" successful'  % (self.mode, filename))
        except:
            #print('%s of "%s" has failed:' % (self.mode, filename), end=' ')
            print(sys.exc_info()[0], sys.exc_info()[1])
        self.mutex.acquire()
        self.threads -= 1
        self.mutex.release()


    def onConnect(self):
        Form.onConnect(self)

        servername = self.content['Server Name'].get()
        portnum    = self.content['Port Number'].get()
        self.portnum = int(portnum)
        self.servername = servername

        print("%s %s" % (servername, portnum))
        # connect to server
        self.connect(servername, int(portnum))



    def onListfiles(self):
        # list files on server
        print("File List:")


    
    def onDownload(self):
        try:
            self.filename = self.listbox.selection_get()
        except:
            print 'no selection'
        # download a file
        print("Starting to download file: %s " % self.filename)
        cmd = "retr " + self.filename 
        self.socket.send(cmd + "\r\n")
        f = self.socket.makefile('r')
        r = self.newdataport(self.servername, self.socket, f)
        while 1:
            code = self.getreply(f)
            if code in ('221', 'EOF'):
                self.socket.send("quit" + "\r\n")
                break
            if code == '150':
                self.getdata(r)
                code = self.getreply(f)
                r = None
         



    def onExit(self):
        if self.threads == 0:
            Tk().quit()
        else:
            tkMessageBox.showinfo(self.title,
                     'Cannot exit: %d threads running' % self.threads)

    def connect(self, servername, portnum):
        #
        # Create control connection
        #
        s = socket(AF_INET, SOCK_STREAM)
        self.socket = s
        s.connect((servername, portnum))
        self.control(servername, s)

    # Control process (user interface and user protocol interpreter).
    #
    def control(self, servername, s):
        #
        # Create control connection
        #
        global FILENAME
        f = s.makefile('r') # Reading the replies is easier from a file...
        #
        # Control loop
        #
        r = None
        while 1:
            code = self.getreply(f)
            print("code = %s" % code)
            if code in ('221', 'EOF'):
                break
            if code == '150':
                self.getdata(r)
                code = self.getreply(f)
                r = None
            if not r:
                r = self.newdataport(servername, s, f)
            cmd = self.getcommand()
            if not cmd: 
                break

            s.send(cmd + "\r\n")
            if cmd.find("retr") != -1:
                FILENAME = cmd[5:]
    

    # Create a new data port and send a PORT command to the server for it.
    # (Cycle through a number of ports to avoid problems with reusing
    # a port within a short time.)


    def newdataport(self, servername, s, f):

        port = self.nextport + self.portnum + 5000
        self.nextport = (self.nextport + 1) % 16
        r = socket(AF_INET, SOCK_STREAM)
        r.bind((servername, port))
        r.listen(1)
        self.sendportcmd(servername, s, f, port)
        self.dataport = r
        return r


    # Send an appropriate port command.
    #
    def sendportcmd(self, servername, s, f, port):
        hostaddr = servername
        hbytes = string.splitfields(hostaddr, '.')
        pbytes = [repr(port//256), repr(port%256)]
        bytes = hbytes + pbytes
        cmd = 'PORT ' + string.joinfields(bytes, ',')
        s.send(cmd + '\r\n')
        code = self.getreply(f)


    # Process an ftp reply and return the 3-digit reply code (as a string).
    # The reply should be a line of text starting with a 3-digit number.
    # If the 4th char is '-', it is a multi-line reply and is
    # terminate by a line starting with the same 3-digit number.
    # Any text while receiving the reply is echoed to the file.
    #
    def getreply(self, f):
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
    def getdata(self, r):
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
    def getcommand(self):
        try:
            while 1:
                line = raw_input('client> ')
                if line: 
                    return line
        except EOFError:
            return ''

class FtpGetfileForm(FtpForm):
    title = 'Client'
    mode  = 'Download'
    def do_transfer(self, filename, servername, remotedir, userinfo):
        #getfile.getfile(filename, servername, remotedir, userinfo, verbose=False, refetch=True)
        pass


# Call the main program.
#
if __name__ == "__main__":
    FtpGetfileForm()
    mainloop()
    #main()