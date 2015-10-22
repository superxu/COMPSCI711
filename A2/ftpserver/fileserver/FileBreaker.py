
# -*- coding: utf-8 -*-
#!/usr/bin/env python


import sys
import os
import io
import hashlib

class StreamBreaker():

    def __init__(self):
      self.width = 10
      self.seed = 2273L
      self.mask = ( 1 << 16 ) - 1
      self.bufferSize = 64 * 1024
      self.hashlist = []
      self.hashdict = {}


    def SetWindowSizeAndMask(self, width, mask):
      self.width = width
      self.mask = mask
    

    def GetSegments(self, filename):
      maxSeed = self.seed
      circle = bytearray(self.width)
      hashvalue = 0L
      circleIndex = 0
      last = 0L
      pos = 0L
      chunks = 0
      m = hashlib.sha1()
      hashdigest = ""
      duplicate = 0
      chunk_index = 0

      length = os.path.getsize(filename)
      readfd = io.open(filename, mode='rb', buffering=-1, encoding=None, errors=None, newline=None, closefd=True)
      filechuncks = ""

      for k in range (0, self.width):
        maxSeed *= maxSeed
        maxSeed &= 0xffffffffffffffff
  

      while True:
        bytesRead = readfd.read(min(self.bufferSize, length-pos))
        for char in bytesRead:
          pos += 1
          hashvalue = ord(char) + ((hashvalue - ( maxSeed * circle[circleIndex] ) ) * self.seed )
          hashvalue &= 0xffffffffffffffff


          circle[circleIndex] = char
          circleIndex += 1

          if circleIndex == self.width:
             circleIndex = 0

          if ((( hashvalue | self.mask ) == hashvalue ) or ( pos == length ) ):
              if circleIndex == 0:
                current_pos =  self.width 
              else:
                current_pos = circleIndex 

              strings = ""
              for i in range(0, current_pos):
                strings += chr(circle[i])
              
              filechuncks += strings
        
              m.update(strings)
              hashdigest = m.hexdigest()
              #print "hash = %s" % hashdigest
              self.hashlist.append(hashdigest)
              if self.hashdict.has_key(hashdigest):
                duplicate += 1
              else:
                chunk_index += 1
                self.hashdict[hashdigest] = chunk_index

              last = pos
              hashvalue = 0
              for j in range(0, self.width):
                 circle[j] = 0

              circleIndex = 0
              chunks += 1
              m = hashlib.sha1()
              sys.stdout.write(filechuncks)

              filename = hashdigest
              writefd = io.open(filename, mode='wb', buffering=-1, encoding=None, errors=None, newline=None, closefd=True)
              writefd.write(filechuncks)
              filechuncks = ""
          
          else:
            if circleIndex == 0:
              values = ''.join(chr(v) for v in circle)
              m.update(values)
              filechuncks += values


        if len(bytesRead) == 0:
           break

      print "chunks = %s"  % chunks
      print "duplicate = %s" % duplicate



def join_chunks(self):
    filelist = os.listdir(".")
    sum = 0
    fd_write =  open("xxx.txt", "wb")
    for i in range(0, len(filelist)):
        if (os.path.isfile(filelist[i])):
            if len(filelist[i]) == 40:
                print "file name is: %s" % filelist[i]
                binary_read = open(filelist[i], "rb")
                count = os.stat(sortfilelist[i]).st_size
                print "count = %s" % count
                sum += count
                content = binary_read.read(count)
                fd_write.write(content)
                binary_read.close()

    print "sum = %s" % sum
    fd_write.close()




def main():
    chunks = StreamBreaker()
    print "filename = %s" % sys.argv[1]
    chunks.SetWindowSizeAndMask(9, (1 << 9) - 1)
    chunks.GetSegments(sys.argv[1])
    chunks.join_chunks()



if __name__ == "__main__":
    main()  



