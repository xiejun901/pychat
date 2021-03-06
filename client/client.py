#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'xiejun'

import socket
import sys
import time

import event_loop
import config


class Connector(event_loop.Event):

    def __init__(self, host, port, loop):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)
        self.fileno = self.sock.fileno()
        self.sock.connect((host,port))
        self.sock.setblocking(0)
        self.buffer = ''
        self.loop = loop
        self.heart_beat_cnt = 0

    def readable(self):
        return True

    def writable(self):
        return len(self.buffer) >0

    def exptable(self):
        return True

    def handle_write_event(self):
        sent = self.sock.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def handle_read_event(self):
        data = self.sock.recv(8192)
        if data:
            print '\033[1;31;m' + data
        else:
            self.close()

    def handle_expt_event(self):
        data = self.sock.recv(1, socket.MSG_OOB)
        self.heart_beat_cnt = 0

    def close(self):
        self.loop.remove_event(self)
        self.sock.close()

class CommandLineClient(event_loop.Event):

    def __init__(self, conn, file, loop):
        self.conn = conn
        self.file = file
        self.fileno = file.fileno()
        self.loop = loop

    def handle_read_event(self):
        self.conn.buffer += (self.file.readline()[:-1]+ '\r\n')

    def readable(self):
        return True

    def writable(self):
        return False

class HeartBeat(event_loop.TaskTimer):

    def __init__(self, conn, expires, period, heart_beat_max):
        event_loop.TaskTimer.__init__(self, expires, period)
        self.conn = conn
        self.heart_beat_max = heart_beat_max

    def callback(self, current):
        self.conn.heart_beat_cnt += 1
        if(self.conn.heart_beat_cnt > self.heart_beat_max):
            self.conn.close()
            exit(0)
        self.conn.sock.send('c', socket.MSG_OOB)



def main():
    argvs  = sys.argv
    if(len(argvs) == 1):
        server_ip = config.serverip
        server_port = config.serverport
    elif (len(argvs) == 3):
        server_ip = argvs[1]
        server_port = int(argvs[2])
    else:
        print 'usage:\n' \
              'python client.py ip port     use the assigned ip and port\n' \
              'python client.py             use configure in config.py\n'
    loop = event_loop.EventLoop()
    connector = Connector(config.serverip, config.serverport, loop)
    cmdline = CommandLineClient(connector, sys.stdin, loop)
    loop.add_event(connector)
    loop.add_event(cmdline)
    loop.add_timer(HeartBeat(connector, time.time()+3, 3, 10))
    loop.loop()


if __name__ == '__main__':
    main()