#!/usr/bin/env python
# coding: utf-8

import sys, posix, string
from socket import *
from form import Form 
from Tkinter import Tk, mainloop
import os
import tkMessageBox

BUFSIZE = 1024


class FtpForm(Form):
    def __init__(self):
        root = Tk()
        root.title(self.title)
        root.geometry("600x600")
        labels = ['Server Name', 'Port Number']
        Form.__init__(self, labels)
        self.portnum = 0
        self.nextport = 0
        self.servername = ""
        self.filename = ""
        self.socket = None
        self.transfer_done = 0
        self.data_transfer_done = 0
        self.filelist = []
    


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
        self.filelist = []
        #print("File List:")
        cmd = "list" 
        self.socket.send(cmd + "\r\n")
        f = self.socket.makefile('r')

        while 1:
            code = self.getreply(f)
            #print("code = %s"  % code)
            if code in ('221', 'EOF'):
                self.socket.send("quit" + "\r\n")
                break
            if code == '150':
                self.getfilelist(self.dataport)
                code = self.getreply(f)

            if self.data_transfer_done == 1:
                self.data_transfer_done = 0
                break

        Form.onListfiles(self, self.filelist)


    
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

        while 1:
            code = self.getreply(f)
            #print("code = %s"  % code)
            if code in ('221', 'EOF'):
                self.socket.send("quit" + "\r\n")
                break
            if code == '150':
                self.getfiledata(self.dataport)
                code = self.getreply(f)

            if self.transfer_done == 1:
                self.transfer_done = 0
                return


    def onExit(self):
        Tk().quit()
  

    def connect(self, servername, portnum):
        s = socket(AF_INET, SOCK_STREAM)
        self.socket = s
        self.socket.connect((servername, portnum))
        self.control(servername)



    # Control process (user interface and user protocol interpreter).
    #
    
    def control(self, servername):
        #
        # Create control connection
        #
        f = self.socket.makefile('r') # Reading the replies is easier from a file...
        #
        # Control loop
        #
        self.dataport = self.newdataport(servername, self.socket, f)
        code = self.getreply(f)
        #print("code = %s" % code)
        if code in ('221', 'EOF'):
            return

        if code == '150':
            self.getfiledata(self.dataport)
            code = self.getreply(f)
            
    

    
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

        if "226" in line:
            self.transfer_done = 1

        #print("line = %s" % line)
        code = line[:3]
        if line[3:4] == '-':
            while 1:
                line = f.readline()
                if not line: 
                    break # Really an error
                #print ("line = %s" % line)
                if line[:3] == code and line[3:4] != '-': break

        return code


    # Get the data from the data connection.
    #
    def getfilelist(self, r):

        #print ('accepting data connection')
        conn, host = r.accept()
        #print ('data connection accepted')
        
        while True:
            data = conn.recv(BUFSIZE)
            if not data: 
                break
            #sys.stdout.write(data)
            self.filelist.append(data)

        self.data_transfer_done = 1
        #print ('end of data connection')


    # Get the data from the data connection.
    #
    def getfiledata(self, r):

        #print ('accepting data connection')
        conn, host = r.accept()
        #print ('data connection accepted')
        
        savefilename = "./downloads" + "/" + self.filename
        writefile = open(savefilename, 'wb')                 # create local file in cwd
        while True:
            data = conn.recv(BUFSIZE)
            if not data:
                 break
            writefile.write(data)

        #print ('end of data connection')


class FtpGetfileForm(FtpForm):
    title = 'Client'
    mode  = 'Download'


# Call the main program.
#
if __name__ == "__main__":
    FtpGetfileForm()
    mainloop()
