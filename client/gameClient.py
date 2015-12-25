__author__ = 'xiejun'

import asyncore
import socket
import logging
import sys
import config

def logConfig(onTerminal):
    #config the logger
    FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,format=FORMAT, filename="client.log", filemode='w')
    logger = logging.getLogger("client_log")

    if onTerminal is True:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)

    return logger


class SenderClient(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.buffer = ''

    def handle_connect(self):
        logger.info("connect to server")

    def handle_close(self):
        self.close()
        logger.info("connection closed")

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        logger.info("send message to server")
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def handle_read(self):
        data = self.recv(8192)
        if data is not None:
            print data


class CommandLineClient(asyncore.file_dispatcher):

    def __init__(self, cli, file):
        asyncore.file_dispatcher.__init__(self,file)
        self.cli = cli

    def handle_read(self):
        self.cli.buffer += (self.recv(1024)[:-1] + '/n/r/n/r')


logger = logConfig(False)
cli = SenderClient(config.serverip, config.serverport)
cmdline = CommandLineClient(cli, sys.stdin)
asyncore.loop()

