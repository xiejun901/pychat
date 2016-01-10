__author__ = 'xiejun'

import socket
import event_loop
import config
import sys
class Connector(event_loop.Event):

    def __init__(self, host, port, loop):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fileno = self.sock.fileno()
        self.sock.connect((host,port))
        self.sock.setblocking(0)
        self.buffer = ''
        self.loop = loop

    def readable(self):
        return True

    def writable(self):
        return len(self.buffer) >0

    def exptable(self):
        return False

    def handle_write_event(self):
        sent = self.sock.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def handle_read_event(self):
        data = self.sock.recv(8192)
        if data:
            print data
        else:
            self.close()

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


def main():
    loop = event_loop.EventLoop()
    connector = Connector(config.serverip, config.serverport, loop)
    cmdline = CommandLineClient(connector, sys.stdin, loop)
    loop.add_event(connector)
    loop.add_event(cmdline)
    loop.loop()

if __name__ == '__main__':
    main()