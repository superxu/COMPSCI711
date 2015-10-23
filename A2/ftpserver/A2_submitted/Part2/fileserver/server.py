#!/usr/bin/env python
# coding: utf-8
# Author: Name: Shupeng Xu  UPI: sxu487   Student ID: 8260026


import os,socket,threading,time
import pickle
from Rabin import StreamBreaker

allow_delete = False
local_ip = "127.0.0.1"
local_port = 8888


class FTPserverThread(threading.Thread):
    def __init__(self,(conn,addr)):
        self.conn = conn
        self.addr = addr
        self.basewd = "./files"
        self.cwd = self.basewd
        self.rest = False
        self.pasv_mode = False
        # existing chunk list
        self.chunklist = []
        self.mode = "I"        # default mode: BINARY
        self.filebreaker = StreamBreaker()
        threading.Thread.__init__(self)

        self.filebreaker.SetWindowSizeAndMask(9, (1 << 9) - 1)

    def run(self):
        self.conn.send('220 Welcome!\r\n')
        while True:
            cmd = self.conn.recv(256)
            if not cmd: 
                break
            else:
                #print 'Recieved:',cmd
                try:
                    func = getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception,e:
                    print 'ERROR:',e
                    self.conn.send('500 Sorry.\r\n')

    def SYST(self,cmd):
        self.conn.send('215 UNIX Type: L8\r\n')
    def OPTS(self,cmd):
        if cmd[5:-2].upper() == 'UTF8 ON':
            self.conn.send('200 OK.\r\n')
        else:
            self.conn.send('451 Sorry.\r\n')
    def USER(self,cmd):
        self.conn.send('331 OK.\r\n')
    def PASS(self,cmd):
        self.conn.send('230 OK.\r\n')
        #self.conn.send('530 Incorrect.\r\n')
    def QUIT(self,cmd):
        self.conn.send('221 Goodbye.\r\n')
    def NOOP(self,cmd):
        self.conn.send('200 OK.\r\n')
    def TYPE(self,cmd):
        self.mode = cmd[5]
        self.conn.send('200 Binary mode.\r\n')

    def CDUP(self,cmd):
        if not os.path.samefile(self.cwd,self.basewd):
            #learn from stackoverflow
            self.cwd = os.path.abspath(os.path.join(self.cwd,'..'))
        self.conn.send('200 OK.\r\n')
    def PWD(self,cmd):
        cwd = os.path.relpath(self.cwd,self.basewd)
        if cwd == '.':
            cwd = '/'
        else:
            cwd = '/' + cwd
        self.conn.send('257 \"%s\"\r\n' % cwd)

    def CWD(self,cmd):
        chwd = cmd[4:-2]
        if chwd =='/':
            self.cwd = self.basewd
        elif chwd[0] == '/':
            self.cwd = os.path.join(self.basewd,chwd[1:])
        else:
            self.cwd = os.path.join(self.cwd,chwd)
        self.conn.send('250 OK.\r\n')

    def PORT(self,cmd):
        if self.pasv_mode:
            self.servsock.close()
            self.pasv_mode = False
        l = cmd[5:].split(',')
        self.dataAddr = '.'.join(l[:4])
        self.dataPort = (int(l[4])<<8)+int(l[5])
        self.conn.send('200 Get port.\r\n')

    def PASV(self,cmd): # from http://goo.gl/3if2U
        self.pasv_mode = True
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.servsock.bind((local_ip,0))
        self.servsock.listen(1)
        ip, port = self.servsock.getsockname()
        print 'open', ip, port
        self.conn.send('227 Entering Passive Mode (%s,%u,%u).\r\n' %
                (','.join(ip.split('.')), port>>8&0xFF, port&0xFF))

    def start_datasock(self):
        if self.pasv_mode:
            self.datasock, addr = self.servsock.accept()
            print 'connect:', addr
        else:
            self.datasock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.datasock.connect((self.dataAddr,self.dataPort))

    def stop_datasock(self):
        self.datasock.close()
        if self.pasv_mode:
            self.servsock.close()


    def LIST(self,cmd):
        self.conn.send('150 Here comes the directory listing.\r\n')
        #print 'list:', self.cwd
        self.start_datasock()
        for t in os.listdir(self.cwd):
            k = self.toListItem(os.path.join(self.cwd,t))
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

    def MKD(self,cmd):
        dn = os.path.join(self.cwd,cmd[4:-2])
        os.mkdir(dn)
        self.conn.send('257 Directory created.\r\n')

    def RMD(self,cmd):
        dn = os.path.join(self.cwd,cmd[4:-2])
        if allow_delete:
            os.rmdir(dn)
            self.conn.send('250 Directory deleted.\r\n')
        else:
            self.conn.send('450 Not allowed.\r\n')

    def DELE(self,cmd):
        fn = os.path.join(self.cwd,cmd[5:-2])
        if allow_delete:
            os.remove(fn)
            self.conn.send('250 File deleted.\r\n')
        else:
            self.conn.send('450 Not allowed.\r\n')

    def RNFR(self,cmd):
        self.rnfn = os.path.join(self.cwd,cmd[5:-2])
        self.conn.send('350 Ready.\r\n')


    def GETC(self, cmd):
        self.conn.send('150 Here comes file chunk list.\r\n')
    
        self.start_datasock()
        k = pickle.dumps(self.filebreaker.hashlist)
        self.datasock.send(k+'\r\n')
        self.stop_datasock()
        self.conn.send('226 File chunk list send OK.\r\n')



    def RETR(self,cmd):
        fn = os.path.join(self.cwd,cmd[5:-2])

        if self.mode == 'I':
            fi = open(fn,'rb')
        else:
            fi = open(fn,'r')

        if fi:
            print 'Downloading:', fn
            # get existing chunks first
            newfilelist = os.listdir(self.filebreaker.chunksdir)
            for chunkname in newfilelist:
                if len(chunkname) == 40:
                    #print "existing chunk name = %s" % chunkname
                    self.chunklist.append(chunkname)

            # break the file into chunks 
            self.filebreaker.filename =  fn
            #print "filename = %s" % self.filebreaker.filename
            self.filebreaker.GetSegments(self.filebreaker.filename)


            self.conn.send('150 Opening data connection.\r\n')
            self.start_datasock()
    

            # compare hashlist with existing chunks
            for value in self.filebreaker.hashlist:
               # print "hash = %s" % value
                if value in self.chunklist:
                    pass
                else:
                    # send chunk to cache
                    filechunkname = self.filebreaker.chunksdir + "/" + value
                    filechunk = open(filechunkname, "rb")
                    data = filechunk.read(1024)

                    while data:
                        self.datasock.send(data)
                        data = filechunk.read(1024)

                    filechunk.close()
                    # add this chunk to existing chunk list
                    self.chunklist.append(value)

            self.stop_datasock()

            # clear chunk list
            #self.filebreaker.hashlist = []
            self.conn.send('226 Transfer complete.\r\n')


        else:
            self.conn.send('500 Sorry.\r\n')



class FTPserver(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((local_ip,local_port))
        threading.Thread.__init__(self)

    def run(self):
        self.sock.listen(5)
        while True:
            th = FTPserverThread(self.sock.accept())
            th.daemon = True
            th.start()

    def stop(self):
        self.sock.close()

if __name__=='__main__':
    ftp = FTPserver()
    ftp.daemon = True
    ftp.start()
    print 'FileServer on', local_ip, ':', local_port
    raw_input('Enter to end...\n')
    ftp.stop()
