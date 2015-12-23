__author__ = 'xiejun'

import asyncore
import asynchat
import socket
import logging
import config

connections = []

def logConfig(onTerminal):
    #config the logger
    FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,format=FORMAT, filename="server.log", filemode='w')
    logger = logging.getLogger("server_log")

    if onTerminal is True:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)

    return logger

class Accepter(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            logger.info("new connection from %s", repr(addr))
            gh = Connector(sock, addr, lobby)
            lobby.addConnector(gh)

    def handle_close(self):
        print 'connect closed'


class Connector(asynchat.async_chat):

    def __init__(self, sock, addr, room):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator('/n/r/n/r')
        self.ibuffer = []
        self.addr = addr
        self.obuffer = ''
        self.room = room


    def collect_incoming_data(self, data):
        '''
        buffer the data
        :param data: the  recieved data
        :return:
        '''
        self.ibuffer.append(data)

    def found_terminator(self):
        '''
        when recieve the terminator
        :return:
        '''
        message = ''.join(self.ibuffer)
        cp = CommandParser()
        if cp.beginWith(message,"/quit"):
            self.quitRoome()
        elif cp.beginWith(message,"/create"):
            li = message.split()
            self.createRoom(li[1])
        for x in self.room.connections:
            x.obuffer += message
        self.ibuffer = []

    def writable(self):
        return (len(self.obuffer) > 0)

    def handle_write(self):
        sent = self.send(self.obuffer)
        self.obuffer = self.obuffer[sent:]


    def handle_close(self):
        '''
        when connection closed
        :return:
        '''
        logger.info('connection closed from %s', repr(self.addr))
        self.close()


    def quitRoome(self):
        self.room.removeConnector(self)
        self.obuffer += ("you are quit room from" + self.room.name)
        if isinstance(self.room, Lobby):
            self.close()
        elif isinstance(self.room, Room):
            if(self.room.empty()):
                lobby.removeRoom(self.room)
            self.room = lobby
            lobby.addConnector(self)
        else:
            raise Exception()

    def createRoom(self, rname):
        self.room.removeConnector(self)
        self.room = Room(rname)
        self.room.addConnector(self)
        lobby.addRoom(self.room)
        self.obuffer += ("you created a room named " + rname + " and enter the new room")

    def joinRoom(self, rname):
        if(isinstance(self.room,Lobby)):
            pass
        elif(isinstance(self.room, Room)):
            self.obuffer += ("you are in a room, you must quit the room to the lobby and enter a new room")
        else:
            raise Exception()


class Room(object):

    def __init__(self, name = "room"):
        self.connections = set()
        self.name = name

    def addConnector(self, conn):
        self.connections.add(conn)

    def removeConnector(self, conn):
        self.connections.remove(conn)

    def empty(self):
        return len(self.connections) == 0

class Lobby(Room):

    def __init__(self, name = "Lobby"):
        Room.__init__(self,name)
        self.rooms = set()

    def addRoom(self, r):
        self.rooms.add(r)

    def removeRoom(self,r):
        self.rooms.remove(r)


class CommandParser(object):

    def beginWith(self, s, t):
        if(len(s) >= len(t) and s[0:len(t)] == t):
            return True
        else:
            return False



lobby = Lobby()
logger = logConfig(False)
gameServer = Accepter(config.serverip, config.serverport)
asyncore.loop()