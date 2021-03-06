#!/usr/bin/env python
    
"""
An echo server that uses select to handle multiple clients at a time.
Entering any line of input at the terminal will exit the server.
"""
    
import select
import socket
import sys
import pycurl, json
import cStringIO
import urllib
import os
import logging
import logging.handlers
from daemon import Daemon

baseurl = ''

def curl(url, data):
    #if not rwfm:
    #    return '{"status":1, "errors":"None"}'
    buf = cStringIO.StringIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, str(url))
    c.setopt(pycurl.HTTPHEADER, ['Accept: application/json','Accept: application/json', 'charsets: utf-8'])
    c.setopt(pycurl.POST, 1)
    #c.setopt(pycurl.POSTFIELDS, json.dumps(data))
    c.setopt(pycurl.POSTFIELDS, urllib.urlencode(data))
    c.setopt(c.WRITEFUNCTION, buf.write)
    c.perform()
    return buf.getvalue()
    
def rwfmd_loop():
    rwfm = 0
    host = ''
    backlog = 500
    size = 1024

    #cfgfile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rwfmd.cfg')
    cfgfile = '/etc/rwfmd.cfg'
    assert os.path.exists(cfgfile), 'Could not find config file %s' % cfgfile
    with open(cfgfile, 'r') as f:
        config = json.loads(f.read())

    port = int(config['rwfmd_port'])
    baseurl = 'http://' + config['webhost'] + ':' + str(config['webport']) + '/rwfm/'


    LOG_FILENAME = '/var/log/rwfmd.log'
    # Set up a specific logger with our desired output level
    logger = logging.getLogger('rwfmLogger')
    logger.setLevel(logging.DEBUG)
    # Add the log message handler to the logger
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=50000, backupCount=5)
    logger.addHandler(handler)


    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host,port))
    server.listen(5)
    input = [server,sys.stdin]
    ret = {}
    running = 1
    while running:
        ret["status"] =1
        ret["errors"] = "None"
        inputready,outputready,exceptready = select.select(input,[],[])
    
        for s in inputready:
    
            if s == server:
                # handle the server socket
                client, address = server.accept()
                input.append(client)
            elif s == sys.stdin:
                # handle standard input
                junk = sys.stdin.readline()
                #running = 0 
            else:
                # handle all other sockets
                data = s.recv(size)
                logger.debug("<= %s", data)
    
                label = {}
                admin  = {}
                obj_id = {}
                olabel = {}
                sub_id = {}
                old_sockid = {}
                slabel = {}
                socklabel = {}
                d=data.split()
                if d[0]=="socket":
                    if(len(d)!=4):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = admin["hostid"] = os.uname()[1]
                    sub_id["uid"] = admin["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    socklabel["sub_id"] = sub_id
                    socklabel["fd"] = d[3]
                    logger.debug(socklabel)
                    if rwfm:
                        ret = json.loads(curl(baseurl+"create/sock/", socklabel))
                    if ret["status"]:
                        logger.debug("\t Socket created")
                    else:
                        logger.debug("\t Socket create failed")
                    s.send(str(ret["status"]))
                elif d[0] in ("connect","bind"):
                    if(len(d)!=6):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = admin["hostid"] = os.uname()[1]
                    sub_id["uid"] = admin["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    sub_id["fd"] = d[3]
                    socklabel["sock_id"] = sub_id
                    if d[0] == "connect":
                        socklabel["server_ip"] = d[4]
                    else:
                        socklabel["ip"] = d[4]
                    socklabel["port"] = d[5]
                    logger.debug(socklabel)
                    if rwfm:
                        if d[0] == "connect":
                            ret = json.loads(curl(baseurl+"connect/", socklabel))
                        else:
                            ret = json.loads(curl(baseurl+"bind/", socklabel))
                    if ret["status"]:
                        logger.debug("\t %s allowed", d[0])
                    else:
                        logger.debug("\t %s not allowed", d[0])
                    s.send(str(ret["status"]))
                elif d[0]=="accept":
                    if(len(d)!=5):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    old_sockid["hostid"] = admin["hostid"] = os.uname()[1]
                    old_sockid["uid"] = admin["uid"] = d[1]
                    old_sockid["pid"] = d[2]
                    old_sockid["fd"] = d[3]
                    socklabel["old_sockid"] = old_sockid
                    socklabel["new_sockfd"] = d[4]
                    logger.debug(socklabel)
                    if rwfm:
                        ret = json.loads(curl(baseurl+"accept/", socklabel))
                    if ret["status"]:
                        logger.debug("\t Accept allowed")
                    else:
                        logger.debug("\t Accept not allowed")
                    s.send(str(ret["status"]))
                elif d[0] in ("send","recv"):
                    if(len(d)!=4):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    socklabel["hostid"] = admin["hostid"] = os.uname()[1]
                    socklabel["uid"] = admin["uid"] = d[1]
                    socklabel["pid"] = d[2]
                    socklabel["fd"] = d[3]
                    logger.debug(socklabel)
                    if rwfm:
                        if d[0]=="send":
                            ret = json.loads(curl(baseurl+"send/", socklabel))
                        else:
                            ret = json.loads(curl(baseurl+"receive/", socklabel))
                    if ret["status"]:
                        logger.debug("\t %s allowed", d[0])
                    else:
                        logger.debug("\t %s not allowed", d[0])
                    s.send(str(ret["status"]))
                elif d[0] == "pipe":
                    if(len(d)!=6):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = admin["hostid"] = os.uname()[1]
                    sub_id["uid"] = admin["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    socklabel["sub_id"] = sub_id
                    fd["fdw"] = d[3]
                    fd["fdr"] = d[4]
                    socklabel["fd"] = fd
                    socklabel["pipe_ref_num"] = d[5]
                    logger.debug(socklabel)
                    if rwfm:
                        ret = json.loads(curl(baseurl+"create/pipe/", socklabel))
                    if ret["status"]:
                        logger.debug("\t %s allowed", d[0])
                    else:
                        logger.debug("\t %s not allowed", d[0])
                    s.send(str(ret["status"]))

                elif d[0] == "mkfifo":
                    if(len(d)!=4):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = admin["hostid"] = os.uname()[1]
                    sub_id["uid"] = admin["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    socklabel["sub_id"] = sub_id
                    socklabel["path"] = d[3]
                    #yet to add pipe_ref_number
                    logger.debug(socklabel)
                    if rwfm:
                        ret = json.loads(curl(baseurl+"make_fifo/", socklabel))
                    if ret["status"]:
                        logger.debug("\t %s allowed", d[0])
                    else:
                        logger.debug("\t %s not allowed", d[0])
                    s.send(str(ret["status"]))
                elif d[0] == "fork":
                    if(len(d)!=4):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = admin["hostid"] = os.uname()[1]
                    sub_id["uid"] = admin["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    slabel["sub_id"] = sub_id
                    slabel["admin"] = admin
                    slabel["parent_pid"] = d[3]
                    if rwfm:
                        ret = json.loads(curl(baseurl+"add/s/", slabel))
                    if ret["status"]:
                        logger.debug("\t created")
                    else:
                        logger.debug("\t create failed")
                    s.send(str(ret["status"]))
    
                elif d[0] in ("exit", "_exit", "_Exit", "exit_group"):
                    if(len(d)!=3):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = os.uname()[1]
                    sub_id["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    if rwfm:
                        ret = json.loads(curl(baseurl+"delete/s/", sub_id))
                    if ret["status"]:
                        logger.debug("\t deleted")
                    else:
                        logger.debug("\t failed delete")
                    s.send(str(ret["status"]))

                elif d[0]=="close":
                    if(len(d)!=4):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = os.uname()[1]
                    sub_id["uid"] = d[1]
                    sub_id["pid"] = d[2]
                    slabel["sub_id"] = sub_id
                    slabel["fd"] = d[3]
                    if rwfm:
                        ret = json.loads(curl(baseurl+"close/", slabel))
                    if ret["status"]:
                        logger.debug("\t closed")
                    else:
                        logger.debug("\t failed close")
                    s.send(str(ret["status"]))
    
                elif d[0]=="rwfm":
                    if(len(d)!=2):
                        logger.debug("\t malformed string for command : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        s.close()
                        input.remove(s)
                        break
                    rwfm = int(d[1])
                    if rwfm==1:
                        logger.debug("\t Enabled rwfm.")
                    else:
                        logger.debug("\t Disabled rwfm.")
                    s.send(str(rwfm))
                elif d[0]in ("open", "open64", "fopen", "fopen64"):
                    if(len(d)!=9):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    #open r|w|rw process_uid process_pid devid inum file_uid file_gid file_mode
                    operation = d[1]
                    sub_id["hostid"] = obj_id["hostid"] = os.uname()[1]
                    obj_id["devid"] = d[4]
                    obj_id["inum"] = d[5]
    
                    sub_id["uid"] = d[2]
                    sub_id["pid"] = d[3]
    
                    olabel["obj_id"] = obj_id
                    olabel["uid"] = d[6]
                    olabel["gid"] = d[7]
                    olabel["mode"] = d[8]
    
                    if rwfm:
                        ret = json.loads(curl(baseurl+"add/o/", olabel))
                    if ret["status"]:
                        logger.debug("\t Added object.")
                        request = {}
                        request["sub_id"] = sub_id
                        request["obj_id"] = obj_id
                        if operation=="r" and rwfm:
                            ret = json.loads(curl(baseurl+"read/", request))
                        elif operation=="w" and rwfm:
                            ret = json.loads(curl(baseurl+"write/", request))
                        elif operation=="rw" and rwfm:
                            ret = json.loads(curl(baseurl+"rdwr/", request))
                        else:
                            ret["status"]=1
                            ret["errors"]="operation undefined."
                        if ret["status"]:
                            logger.debug("\t %s allowed.", operation)
                        else:
                            logger.debug("\t %s not allowed.", operation)
                        s.send(str(ret["status"])) #send request status.
                    else:
                        print "\nadd failed"
                        s.send(str(ret["status"])) #send object add status.
    
                elif d[0] in ("rename", "renameat"):
                    if(len(d)!=7):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = obj_id["hostid"] = os.uname()[1]
                    sub_id["uid"] = d[1]
                    sub_id["pid"] = d[2]
    
                    obj_id["devid"] = d[3]
                    obj_id["inum"] = d[4]
  
                    if rwfm:
                        ret = json.loads(curl(baseurl+"delete/o/", obj_id))
                    if ret["status"]:
                        logger.debug("\t Deleted original object.")
                    else:
                        logger.debug("\t Original object delete failed.")
    
                    obj_id["devid"] = d[5]
                    obj_id["inum"] = d[6]
    
                    label["sub_id"] = sub_id
                    label["obj_id"] = obj_id

                    if rwfm:
                        ret = json.loads(curl(baseurl+"create/o/", label))
                    if ret["status"]:
                        logger.debug("\t Created renamed object.")
                    else:
                        logger.debug("\t Create failed for renamed object.")
    
                    s.send(str(ret["status"])) #send object create status.
    
                elif d[0]in ("creat", "mkdir", "link", "linkat", "symlink", "symlinkat"):
                    if(len(d)!=5):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.close()
                        input.remove(s)
                        break
                    sub_id["hostid"] = obj_id["hostid"] = os.uname()[1]
                    sub_id["uid"] = d[1]
                    sub_id["pid"] = d[2]
    
                    obj_id["devid"] = d[3]
                    obj_id["inum"] = d[4]
    
                    label["sub_id"] = sub_id
                    label["obj_id"] = obj_id
    
                    if rwfm:
                        if d[0] in ("link", "linkat"):#hardlinks have same inum/devid.
                            ret = json.loads(curl(baseurl+"delete/o/", obj_id))

                        ret = json.loads(curl(baseurl+"create/o/", label))
                        if ret["status"]:
                            logger.debug("\t Created object.")
                        else:
                            logger.debug("\t Create failed.")
    
                    s.send(str(ret["status"])) #send object create status.
    
                elif d[0]in ("unlink", "unlinkat", "rmdir"):
                    if(len(d)!=3):
                        logger.debug("\t malformed string for syscall : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    obj_id["hostid"] = os.uname()[1]
                    obj_id["devid"] = d[1]
                    obj_id["inum"] = d[2]
                    if rwfm: 
                        ret = json.loads(curl(baseurl+"delete/o/", obj_id))
                    if ret["status"]:
                        logger.debug("\t Deleted object.")
                    else:
                        logger.debug("\t Delete failed.")
                    s.send(str(ret["status"])) #send object add status.
    
                elif d[0]=="stop":
                    if(len(d)!=1):
                        logger.debug("\t malformed string for command : %s", d[0])
                        s.send("1")
                        s.close()
                        input.remove(s)
                        break
                    #curl(url, d)
                    s.send(data)
                    running = 0
                s.close()
                input.remove(s)
    
    server.close()


class rwfmDaemon(Daemon):
        def run(self):
            rwfmd_loop()

if __name__ == "__main__":
        daemon = rwfmDaemon('/tmp/rwfmd.pid')
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                elif 'loop' == sys.argv[1]:
                        rwfmd_loop()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart|loop" % sys.argv[0]
                sys.exit(2)

