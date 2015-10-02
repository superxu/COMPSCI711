#!/usr/bin/env python
# Author: Name: Shupeng Xu  UPI: sxu487   Student ID: 8260026

import sys
import os
import json
import time
import datetime


def check_cachelog_in_dir(dirname):
    if not os.path.exists(dirname + "/" + "fileinfo.log"): 
        return False

    return True


def check_requestlog_in_dir(dirname):
    if not os.path.exists(dirname + "/" + "requestinfo.log"): 
        return False

    return True


def same_mtimes(t1, t2):
    return (t1 == t2)



def compare_mtime(t1, t2):
    return (t1 > t2)




def get_requestlog_content(dirname):
    requestlog = dirname + "/"+ "requestinfo.log"
    values = {}

    if not os.stat(requestlog).st_size == 0:
        fd_read =  open(requestlog, "r")
        values = json.load(fd_read)
        fd_read.close()

    return values


def get_cachelog_content(dirname):
    cachelog = dirname + "/"+ "fileinfo.log"
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


def write_cacheinfo_tofile(dirname, new_values):
    newfilelist = os.listdir(dirname)
    cachelog = dirname + "/"+ "fileinfo.log"

    # get history values first
    old_values = get_cachelog_content(dirname)

    if (os.stat(cachelog).st_size == 0) or (is_empty(old_values)):
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


# add new key/value pair
# find exisited key and extend it
def update_cachelog(dirname, key,  new_value):
    cachelog = dirname + "/"+ "fileinfo.log"

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

    cachelog = dirname + "/"+ "fileinfo.log"
    loginfo = {}


    for i in range(0, len(filelist)):

        if (os.path.isfile(dirname + "/" + filelist[i])):
            # do not create info of fileinfo.log file
            if (filelist[i] == "fileinfo.log") or (filelist[i] == "requestinfo.log"):   
                pass
            else:  
                last_modified = time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime(os.path.getmtime(dirname + "/"+ filelist[i])))

                valuelist = []
                valuelist.append(last_modified)

                loginfo.setdefault(filelist[i], []).append(valuelist)
             
        # do not process directories
        else:
            pass

    # write SHA256 value to fileinfo.log file
    write_cacheinfo_tofile(dirname, loginfo)


def create_cachelog(dirname):
    if not check_cachelog_in_dir(dirname):
    	os.system("touch fileinfo.log")
  

def create_requestlog(dirname):
    if not check_requestlog_in_dir(dirname):
        os.system("touch requestinfo.log")


def update_requestlog(dirname, filename,  hit):
   
    requestlog = dirname + "/"+ "requestinfo.log"
    origin_values = get_requestlog_content(dirname)

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



def downloadfilefromserver(filename):
    pass


# find out if the file requested is in the directory(cache) and response.
def process_request(dirname, filename):

    cachelog = dirname + "/" + "fileinfo.log"
    # get log info values 
    loginfo = get_cachelog_content(dirname)

    if not is_empty(loginfo):
        # file exists
        if loginfo.has_key(filename):
            # update request log
            update_requestlog(dirname, filename, True)
        # file does not exist
        else:
            downloadfilefromserver(filename)
            # update request log
            update_requestlog(dirname, filename, False)
            pass

    # no files in the cache
    else:
        print("Empty cache....")
        update_requestlog(dirname, filename, False)
        pass



def main():

    dirname = "."
    create_cachelog(dirname)
    create_requestlog(dirname)
    # generate log of files in the directory
    gen_dir_loginfo(dirname)

    process_request(dirname, sys.argv[1])
    


if __name__ == "__main__":
    main()

