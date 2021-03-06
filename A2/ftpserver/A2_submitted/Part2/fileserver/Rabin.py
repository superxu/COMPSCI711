# -*- coding: utf-8 -*-
#!/usr/bin/env python
# Author: Name: Shupeng Xu  UPI: sxu487   Student ID: 8260026



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
      self.filename = ""
      self.chunksdir = "./chunks"


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
      self.hashlist = []

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

              last = pos
              hashvalue = 0
              for j in range(0, self.width):
                 circle[j] = 0

              circleIndex = 0
              chunks += 1
              m = hashlib.sha1()
              #sys.stdout.write(filechuncks)

              filename = "chunks" + "/" + hashdigest
              writefd = io.open(filename, mode='wb', buffering=-1, encoding=None, errors=None, newline=None, closefd=True)
              # put hash value at the last of the chunk
              filechuncks += hashdigest

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





def main():
    chunks = StreamBreaker()
    #print "filename = %s" % sys.argv[1]
    chunks.SetWindowSizeAndMask(9, (1 << 9) - 1)
    chunks.filename = "files" + "/" + sys.argv[1]
    print "filename = %s" % chunks.filename
    chunks.GetSegments(chunks.filename)


if __name__ == "__main__":
    main()  