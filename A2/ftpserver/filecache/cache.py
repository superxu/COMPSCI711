#!/usr/bin/env python
# Author: Name: Shupeng Xu  UPI: sxu487   Student ID: 8260026


import sys
import os
import json
import time
import datetime
import shutil

   


def check_cachelog_in_dir(dirname):
    if not os.path.exists(dirname + "/" + "cache.log"): 
        return False

    return True



def same_mtimes(t1, t2):
    return (t1 == t2)



def compare_mtime(t1, t2):
    return (t1 > t2)



def get_cachelog_content(dirname):
    cachelog = dirname + "/"+ "cache.log"
    values = {}

    if not os.stat(cachelog).st_size == 0:
        fd_read =  open(cachelog, "r")
        values = json.load(fd_read)
        fd_read.close()

    return values



def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True


def write_info_tofile(dirname, new_values):
    newfilelist = os.listdir(dirname)
    cachelog = dirname + "/"+ "cache.log"

    # get history values first
    old_values = get_cachelog_content(dirname)

    if (os.stat(cachelog).st_size == 0) or (is_empty(old_values)):
        fd_write_first =  open(cachelog, "w")
        json.dump(new_values, fd_write_first, indent=8)
        fd_write_first.close()
   
    else:
        fd_write =  open(cachelog, "w")
        for i in range(0, len(newfilelist)):
            if newfilelist[i] == "cache.log":   
                pass
            else: 
                if (os.path.isfile(dirname + "/" + newfilelist[i])):
                    # new file added
                    old_values[newfilelist[i]] = new_values[newfilelist[i]]
    


        json.dump(old_values, fd_write, indent=8)
        fd_write.close()





# add new key/value pair
# find exisited key and extend it
def update_cachelog(dirname, key,  new_value):
    cachelog = dirname + "/"+ "cache.log"

    # get history values first
    origin_values = get_cachelog_content(dirname)


    if not (key in origin_values.keys()):
        fd_write_first =  open(cachelog, "w")
        origin_values[key] = [new_value]
        json.dump(origin_values, fd_write_first, indent=8)
        fd_write_first.close()

    else:
        fd_write =  open(cachelog, "w")
        origin_values[key].extend([new_value]) 
        # it seems nothing wrong with reverse or sort. even I comment reverse() below, the position/order of keys may still change
        origin_values[key].reverse()     
        json.dump(origin_values, fd_write, indent=8)
        fd_write.close()



def gen_dir_loginfo(dirname):

    filelist = os.listdir(dirname)

    if len(filelist) == 0:
        return

    cachelog = dirname + "/"+ "cache.log"
    sha256_values = {}


    for i in range(0, len(filelist)):

        if (os.path.isfile(dirname + "/" + filelist[i])):
            # do not create info of cache.log file
            if filelist[i] == "cache.log":   
                pass
            else:  
                last_modified = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(os.path.getmtime(dirname + "/"+ filelist[i])))

                valuelist = []
                valuelist.append(last_modified)

                sha256_values.setdefault(filelist[i], []).append(valuelist)
             
        # do not process directories
        else:
            pass

    # write SHA256 value to cache.log file
    write_info_tofile(dirname, sha256_values)



def create_cachelog(dirname):
    if not check_cachelog_in_dir(dirname):
    	os.system("touch cache.log")
  


def main():

    create_cachelog(".")
    # generate SHA256 of files in the directory
    gen_dir_loginfo(".")

    


if __name__ == "__main__":
    main()

