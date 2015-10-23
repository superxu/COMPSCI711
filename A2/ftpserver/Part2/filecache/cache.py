#!/usr/bin/env python
# Author: Name: Shupeng Xu  UPI: sxu487   Student ID: 8260026

import sys
import os
import json
import time
import datetime
import posix, string
import threading
import socket
from form import Form 
from Tkinter import Tk, mainloop
import tkMessageBox
import pickle


HOSTNAME = "127.0.0.1"
BUFSIZE = 1024

# Default port numbers used by the FTP protocol.
#
FTP_PORT = 8888
FTP_DATA_PORT = FTP_PORT - 1

# Change the data port to something not needing root permissions.
#
FTP_DATA_PORT = FTP_DATA_PORT + 50000

DIRNAME = "./cachefiles"
CACHELOG = "./cachefiles/fileinfo.log"
REALSERVER_DIRNAME = "./files"
CHUNKSDIR = "./cachechunks"


class FtpForm(Form):
    def __init__(self):
        root = Tk()
        root.title(self.title)
        root.geometry("600x600")
        Form.__init__(self)
   

        self.portnum = 0
        self.nextport = 0
        self.servername = ""
        self.filename = ""
        self.socket = None
        self.transfer_done = 0
        self.data_transfer_done = 0
     


    def onListfiles(self):
        # list files on server
        print("File List:")
        self.filelist = os.listdir(DIRNAME)

        Form.onListfiles(self, self.filelist)


    
    def onShowlog(self):
        fd = open(CACHELOG, "r")
        data = json.load(fd)
        print data
        Form.onShowlog(self, data)



    def onExit(self):
        Tk().quit()


class CacheClient():
   
    def __init__(self):
        self.buffersize = BUFSIZE
        self.ctrl_portnum = FTP_PORT
        self.data_portnum = FTP_DATA_PORT
        self.hostname = HOSTNAME
        self.filename = ""
        self.dirname = ""
        self.nextport = 0
        self.downloadok = False
        self.listfilesok = False
        self.getchunklistok = False
        self.socket = None
        self.filelist = []
        self.filechunklist = []
        self.chunksdir = CHUNKSDIR
        self.savefilename = ""
        self.requestfile = ""


    def downloadfilefromserver(self):
        self.control()
        self.getfilechunklistfromserver()
        self.splitfileintochunks()
        self.join_chunks()
        return self.downloadok


    def getfilelistfromserver(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.hostname, self.ctrl_portnum))
        f =  self.socket.makefile('r') # Reading the replies is easier from a file...
        #
        # Control loop
        #
        r = None
        while 1:
            code = self.getreply(f)
            if code in ('221', 'EOF', '500'):
                print("Fail to list files...")
                self.listfilesok = False
                break

            if code == '150':
                self.getfilelistdata(r)
                if self.listfilesok  == True:
                    self.socket.send("quit" + "\r\n")
                    break
                code = self.getreply(f)
                r = None
            if not r:
                r = self.newdataport(self.socket, f)

            cmd = "list"
            print("cmd = %s" % cmd)
            if not cmd: 
                break

            self.socket.send(cmd + "\r\n")


    def getfilechunklistfromserver(self):

        f =  self.socket.makefile('r') # Reading the replies is easier from a file...
        #
        # Control loop
        #
        r = None
        while 1:
            code = self.getreply(f)
            print "file chunk code = %s" % code
            if code in ('221', 'EOF', '500'):
                print("Fail to get file chunks...")
                break

            if code == '150':
                self.getfilechunklist(r)
                if self.getchunklistok == True:
                    self.socket.send("quit" + "\r\n")
                    break
                code = self.getreply(f)
                r = None
            if not r:
                r = self.newdataport(self.socket, f)

            if code == "226":
                pass
            else:
                cmd = "getc"
                print("cmd = %s" % cmd)
                self.socket.send(cmd + "\r\n")


    # Control process (user interface and user protocol interpreter).
    #
    def control(self):
        f =  self.socket.makefile('r')
        r = None
        while 1:
            code = self.getreply(f)
            print "control code = %s" % code
            if code in ('221', 'EOF', '500'):
                print("Fail to download file...")
                self.downloadok = False
                break

            if code == '150':
                self.getdata(r)
                if self.downloadok == True:
                    self.socket.send("quit" + "\r\n")
                    break
                code = self.getreply(f)
                r = None

            if not r:
                r = self.newdataport(self.socket, f)

            if code in "226":
                pass
            else:
                cmd = "retr " + self.filename  
                print("cmd = %s" % cmd)
                self.socket.send(cmd + "\r\n")

    # Create a new data port and send a PORT command to the server for it.
    # (Cycle through a number of ports to avoid problems with reusing
    # a port within a short time.)
    #
   
    def newdataport(self, s, f):
        port = self.nextport + self.data_portnum
        self.nextport = (self.nextport + 1) % 16
        r = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        r.bind((self.hostname, port))
        r.listen(1)
        self.sendportcmd(s, f, port)
        return r


    # Send an appropriate port command.
    #
    def sendportcmd(self, s, f, port):

        hostaddr = self.hostname
        hbytes = string.splitfields(hostaddr, '.')
        pbytes = [repr(port//256), repr(port%256)]
        bytes = hbytes + pbytes
        cmd = 'PORT ' + string.joinfields(bytes, ',')
        s.send(cmd + '\r\n')
        code = self.getreply(f)



    def getreply(self, f):
        line = f.readline()
        if not line: 
            return 'EOF'

        code = line[:3]
        if line[3:4] == '-':
            while 1:
                line = f.readline()
                if not line: 
                    break # Really an error
                if line[:3] == code and line[3:4] != '-': break

        return code


    # Get the data from the data connection.
    #
    def getfilelistdata(self, r):
        self.filelist = []
        conn, host = r.accept()
        
        while True:
            data = conn.recv(BUFSIZE)
            if not data: 
                break

            sys.stdout.write(data)
            self.filelist.append(data)

        self.listfilesok = True
    


    def getfilechunklist(self, r):
        self.filechunklist = []
        string = ''
        conn, host = r.accept()
        print "getfilechunklist"

        while True:
            data = conn.recv(BUFSIZE)
            if not data: 
                break

            string += data

        self.filechunklist = pickle.loads(string)
        self.getchunklistok = True




    def join_chunks(self):
        filelist = self.filechunklist
        sum = 0
        fd_write =  open(DIRNAME + "/" + self.requestfile, "wb")

        for i in range(0, len(filelist)):
            filename = CHUNKSDIR + "/" + filelist[i]
            if (os.path.isfile(filename)):
                if len(filelist[i]) == 40:
                    #print "file name is: %s" % filelist[i]
                    binary_read = open(filename, "rb")
                    count = os.stat(filename).st_size
                    sum += count
                    content = binary_read.read(count)
                    fd_write.write(content)
                    binary_read.close()

        print "sum = %s" % sum
        fd_write.close()

        # clear file chunk list
        self.filechunklist = []




    def splitfileintochunks(self):
        # split file into chunks and remove original file
        filenamelist = []
        fileoffset = [0]
        filelength = []
        readfd = open(self.savefilename, "r")
        filecontent = readfd.read()
        num = 0

        for hashvalue in self.filechunklist:
            print "hashvalue = %s" % hashvalue
            if hashvalue in filecontent:
                filenamelist.append(hashvalue)
                print "found hashvalue = %s" % hashvalue
                offset = filecontent.index(hashvalue) + 40
                print "offset = %s" % offset
                fileoffset.append(offset)

        

        for i in range(0, len(fileoffset)-1):
            length = fileoffset[i+1] - fileoffset[i] - 40
            filelength.append(length)


        
        for filename in filenamelist:
            writefd = open(CHUNKSDIR + "/" + filename, "wb")
            readfd.seek(fileoffset[num])
            data = readfd.read(filelength[num])
            writefd.write(data)
            writefd.close()
            num += 1
        
        
        readfd.close()
        


    # Get the data from the data connection.
    #
    def getdata(self, r):
        conn, host = r.accept()
        filename = self.chunksdir + "/" + self.filename

        filefd = open(filename, 'wb')                 # create local file in cwd
        while True:
            data = conn.recv(self.buffersize)
            if not data:
                 break
            filefd.write(data)

        filefd.close()


        self.downloadok = True
        self.savefilename = filename
        self.requestfile = self.filename
        self.filename = ""




SERVER_PORT = 3333     # use different port as real server does

class CacheServerThread(threading.Thread):
    def __init__(self, (conn,addr)):
        self.conn = conn
        self.addr = addr
        self.basewd = './cachefiles'
        self.cwd = self.basewd
        self.pasv_mode = False
        self.mode = "I"        # default mode: BINARY
        threading.Thread.__init__(self)
        self.requestfilename = ""
        self.client = CacheClient()

    def run(self):
        self.conn.send('220 Welcome!\r\n')
        while True:
            cmd = self.conn.recv(256)
            if not cmd: 
                break
            else:
                print 'Recieved:',cmd
                try:
                    func = getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception,e:
                    print 'ERROR:',e
                    self.conn.send('500 Sorry.\r\n')

    def QUIT(self,cmd):
        self.conn.send('221 Goodbye.\r\n')

    def NOOP(self,cmd):
        self.conn.send('200 OK.\r\n')


    def PORT(self,cmd):
        if self.pasv_mode:
            self.servsock.close()
            self.pasv_mode = False

        l = cmd[5:].split(',')
        self.dataAddr = '.'.join(l[:4])
        self.dataPort = (int(l[4])<<8)+int(l[5])
        self.conn.send('200 Get port.\r\n')


    def start_datasock(self):
        if self.pasv_mode:
            self.datasock, addr = self.servsock.accept()
            print 'connect:', addr
        else:
            self.datasock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.datasock.connect((self.dataAddr,self.dataPort))

    def stop_datasock(self):
        self.datasock.close()
        if self.pasv_mode:
            self.servsock.close()


    # forward this to real server
    def LIST(self, cmd):

        # get file list form real server and send it to client
        self.client.hostname = HOSTNAME

        self.client.getfilelistfromserver()

        if  self.client.listfilesok == True:
            self.conn.send('150 Here comes the directory listing.\r\n')

            self.start_datasock()
           
            for k in self.client.filelist:
                self.datasock.send(k+'\r\n')
            
            self.stop_datasock()
            self.conn.send('226 Directory send OK.\r\n')




    def toListItem(self,fn):
        st = os.stat(fn)
        fullmode ='rwxrwxrwx'
        mode =''
        for i in range(9):
            mode += ((st.st_mode>>(8-i))&1) and fullmode[i] or '-'

        d = (os.path.isdir(fn)) and 'd' or '-'
        ftime = time.strftime(' %b %d %H:%M ', time.gmtime(st.st_mtime))
        return d + mode + ' 1 user group ' + str(st.st_size) + ftime + os.path.basename(fn)



    def SEND_DATA_TO_CLIENT(self, filename):
        print 'Downloading:', filename
       
        # join chunks into a complete file and send it to the client



        if self.mode == 'I':
            fi = open(filename,'rb')
        else:
            fi = open(filename,'r')
       

        self.conn.send('150 Opening data connection.\r\n')
       
        data = fi.read(1024)
        self.start_datasock()
      
        while data:
            self.datasock.send(data)
            data = fi.read(1024)
        
        fi.close()
        self.stop_datasock()
        self.conn.send('226 Transfer complete.\r\n')






    # received download request
    def RETR(self, cmd):
        # check if the file exists in cache
        self.requestfilename = os.path.join(self.cwd, cmd[5:-2])
        self.getfilename = cmd[5:-2]
        print("request file name = %s" % self.requestfilename)

        # check if requested file in cache
        result = self.process_request(self.cwd, self.requestfilename)
        # found file in cache, send data to client
        if result == True:
            self.SEND_DATA_TO_CLIENT(self.requestfilename)
        else:
            # I am now a client
            self.client.hostname = HOSTNAME
            self.client.filename = self.getfilename
            self.client.dirname = DIRNAME

            self.client.downloadfilefromserver()

            if  self.client.downloadok == True:
                self.SEND_DATA_TO_CLIENT(self.requestfilename)
                self.update_cachelog(self.cwd, self.requestfilename)

            #cannot find requested file in real server
            else:
                # delete revelant entries
                self.delete_requestlog_entry(self.requestfilename)
                self.conn.send('500 Sorry.\r\n')


    def delete_requestlog_entry(self, entry):
        requestlog = self.cwd + "/"+ "requestinfo.log"
        origin_values = self.get_requestlog_content(self.cwd)
        print("before pop = %s" % origin_values)
        print("entry = %s" % entry)

        if origin_values.has_key(entry):  
            origin_values.pop(entry, None)   
            print("after pop = %s" % origin_values )

        fd_write =  open(requestlog, "w")
        json.dump(origin_values, fd_write, indent=8)
        fd_write.close()   


    def get_cachelog_content(self, dirname):
        cachelog = dirname + "/"+ "fileinfo.log"
        values = {}

        if not os.stat(cachelog).st_size == 0:
            fd_read =  open(cachelog, "r")
            values = json.load(fd_read)
            fd_read.close()

        return values


    def get_requestlog_content(self, dirname):
        requestlog = dirname + "/"+ "requestinfo.log"
        values = {}

        if not os.stat(requestlog).st_size == 0:
            fd_read =  open(requestlog, "r")
            values = json.load(fd_read)
            fd_read.close()

        return values


    # if file not in cache and download successfully from real server
    def update_cachelog(self, dirname, filename):
       
        print "update_cachelog filename = %s" % filename
        cachelog = dirname + "/"+ "fileinfo.log"
        origin_values = self.get_cachelog_content(dirname)

        download_time = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime())
        fileinfo = {}

        valuelist = []
        valuelist.append(download_time)

        if origin_values.has_key(filename):
            fd_write =  open(cachelog, "w")
            origin_values[filename].extend([valuelist]) 
            origin_values[filename].reverse()     
            json.dump(origin_values, fd_write, indent=8)
            fd_write.close()
        else:
            fileinfo.setdefault(filename, []).append(valuelist)
            fd_write_first =  open(cachelog, "w")
            origin_values[filename] = fileinfo[filename]
            json.dump(origin_values, fd_write_first, indent=8)
            fd_write_first.close()



    def update_requestlog(self, dirname, filename,  hit):
       
        requestlog = dirname + "/"+ "requestinfo.log"
        origin_values = self.get_requestlog_content(dirname)

        request_time = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime())
        requestinfo = {}

        user_request = "user request:" + " file "  + filename + " at " + request_time
        if hit == True:
            response = "response:" + " cached file " + filename
        else:
            response = "response:" + " file " + filename  + " downloaded from the server"

        valuelist = []
        valuelist.append(user_request)
        valuelist.append(response)

        if origin_values.has_key(filename):
            fd_write =  open(requestlog, "w")
            origin_values[filename].extend([valuelist]) 
            # it seems nothing wrong with reverse or sort. even I comment reverse() below, the position/order of keys may still change
            origin_values[filename].reverse()     
            json.dump(origin_values, fd_write, indent=8)
            fd_write.close()
        else:
            requestinfo.setdefault(filename, []).append(valuelist)
            fd_write_first =  open(requestlog, "w")
            origin_values[filename] = requestinfo[filename]
            json.dump(origin_values, fd_write_first, indent=8)
            fd_write_first.close()





    # find out if the file requested is in the directory(cache) and response.
    def process_request(self, dirname, filename):

        cachelog = dirname + "/" + "fileinfo.log"
        # get log info values 
        loginfo = self.get_cachelog_content(dirname)

        if loginfo:
            # file exists
            if loginfo.has_key(filename):
                self.update_requestlog(dirname, filename, True)
                return True
            # file does not exist
            else:
                self.update_requestlog(dirname, filename, False)
                return False

        # no files in the cache
        else:
            print("Empty cache....")
            self.update_requestlog(dirname, filename, False)
            return False



class CacheServer(threading.Thread):
   
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((HOSTNAME, SERVER_PORT))
        threading.Thread.__init__(self)


    def run(self):
        self.sock.listen(5)
        while True:
            th = CacheServerThread(self.sock.accept())
            th.daemon = True
            th.start()


    def stop(self):
        self.sock.close()




# create a log to record files in the cache
class CacheLog():


    def __init__(self):
        pass


    def check_cachelog_in_dir(self, dirname):
        if not os.path.exists(dirname + "/" + "fileinfo.log"): 
            return False

        return True


    def check_requestlog_in_dir(self, dirname):
        if not os.path.exists(dirname + "/" + "requestinfo.log"): 
            return False

        return True


    def is_empty(self, any_structure):
        if any_structure:
            return False
        else:
            return True

    def get_cachelog_content(self, dirname):
        cachelog = dirname + "/"+ "fileinfo.log"
        values = {}

        if not os.stat(cachelog).st_size == 0:
            fd_read =  open(cachelog, "r")
            values = json.load(fd_read)
            fd_read.close()

        return values


    def write_cacheinfo_tofile(self, dirname, new_values):
        newfilelist = os.listdir(dirname)
        cachelog = dirname + "/"+ "fileinfo.log"

        # get history values first
        old_values = self.get_cachelog_content(dirname)

        if (os.stat(cachelog).st_size == 0) or (self.is_empty(old_values)):
            fd_write_first =  open(cachelog, "w")
            json.dump(new_values, fd_write_first, indent=8)
            fd_write_first.close()
       
        else:
            fd_write =  open(cachelog, "w")
            for i in range(0, len(newfilelist)):
                if (newfilelist[i] == "fileinfo.log") or (newfilelist[i] == "requestinfo.log"):   
                    pass
                else: 
                    if (os.path.isfile(dirname + "/" + newfilelist[i])):
                        # new file added
                        old_values[newfilelist[i]] = new_values[newfilelist[i]]
        


            json.dump(old_values, fd_write, indent=8)
            fd_write.close()



    def gen_dir_loginfo(self, dirname):

        filelist = os.listdir(dirname)

        if len(filelist) == 0:
            return

        cachelog = dirname + "/"+ "fileinfo.log"
        loginfo = {}


        for i in range(0, len(filelist)):
            if (os.path.isfile(dirname + "/" + filelist[i])):
                # do not create info of fileinfo.log file
                if (filelist[i] == "fileinfo.log") or (filelist[i] == "requestinfo.log"):   
                    pass
                else:  
                    # time not used in log file
                    last_modified = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(os.path.getmtime(dirname + "/"+ filelist[i])))

                    valuelist = []
                    valuelist.append(last_modified)

                    loginfo.setdefault(filelist[i], []).append(valuelist)
                 
            # do not process directories
            else:
                pass

        # write value to fileinfo.log file
        self.write_cacheinfo_tofile(dirname, loginfo)


    def create_cachelog(self, dirname):
        if not self.check_cachelog_in_dir(dirname):
            filename = dirname + "/" + "fileinfo.log"
            create_file = "touch %s" % filename
            os.system(create_file)
      

    def create_requestlog(self, dirname):
        if not self.check_requestlog_in_dir(dirname):
            filename = dirname + "/"+ "requestinfo.log"
            create_file = "touch %s" % filename
            os.system(create_file)



class FtpGetfileForm(FtpForm):
    title = 'CacheServer'
    mode  = 'Download'



# cache should be both a client and a server
def createfiles():
    cachelog = CacheLog()
    dirname = DIRNAME
    cachelog.create_cachelog(dirname)
    cachelog.create_requestlog(dirname)



def main():
    cacheserver = CacheServer()
    cacheserver.daemon = True
    cacheserver.start()
    print 'Cache Server on', HOSTNAME, ':', SERVER_PORT
    raw_input('Enter to end...\n')
    cacheserver.stop()
    


if __name__ == "__main__":
    createfiles()
    FtpGetfileForm()
    main()
    mainloop()


