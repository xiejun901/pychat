__author__ = 'xiejun'

import asyncore
import asynchat
import socket
import logging
import config
from accountInfo import AccountInfo
import time

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
            gh = Connector(sock, addr)

    def handle_close(self):
        logger.info("connect closed")


class Connector(asynchat.async_chat):

    def __init__(self, sock, addr):
        asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator('/n/r/n/r')
        self.ibuffer = []
        self.addr = addr
        self.obuffer = ''
        self.name = None


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
        self.ibuffer = []
        cp = CommandParser()
        if cp.beginWith(message, '/CREATE'):
            pass
        elif cp.beginWith(message, '/SIGNIN'):
            self.signIN(message)
        elif cp.beginWith(message, '/SIGNOUT'):
            self.signOut(message)
        elif cp.beginWith(message, '/CHATROOM'):
            pass
        elif cp.beginWith(message, '/CHATALL'):
            pass
        elif cp.beginWith(message, '/CHATTO'):
            pass
        else:
            pass


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

    def checkUserCount(self, name, password):
        if (name in userCount and userCount[name] == password):
            return True
        else:
            return False

    def signIN(self, message):
        """
        :param message: str
        :return:
        :type message: str
        """
        li = message.split(' ', 2)
        if len(li) < 3:
            self.sendMessage('system: wrong account or password')
            return
        accountName = li[1]
        passWord = li[2]
        if (accountName in userCount and userCount[accountName].PassWord == passWord):
            userCount[accountName].connection = self
            userCount[accountName].logInTime = time.time()
            lobby.addAccount(userCount[accountName])
            self.name = accountName
        else:
            self.sendMessage('system: wrong account or password')

    def chatRoom(self, message):
        """
        chat to room
        :param message:
        :return:
        """
        li = message.split(' ', 1)
        room = userCount[self.name]

    def signOut(self, message):
        """
        sign out
        :param message: str
        :return:
        """
        accInfo = userCount[self.name]
        accInfo.room.removeAccount(accInfo)


    def sendMessage(self, message):
        """
        send message to client
        :param message: str
        :return:
        """
        self.obuffer += message

class Room(object):

    def __init__(self, name = "room"):
        """
        :param name: str
        :return: None
        """
        self.connections = set()
        self.name = name
        self.accounts = {}

    def addAccount(self, accountInfo):
        """
        :param accountInfo:
        :return:
        :type accountName: string
        :type accountInfo: AccountInfo
        """
        accountName = accountInfo.accountName
        for accInfo in self.accounts.values():
            accInfo.connection.sendMessage(accountName + ' join the room')
        self.accounts[accountName] = accountInfo
        accountInfo.room = self
        accountInfo.connection.sendMessage('system: welcome to join room( ' + self.name + ')! you can quit the room by enter "/quit"\n')

    def removeAccount(self, accountInfo):
        """

        :param accountInfo:
        :return:
        """
        accountInfo.room = None
        accountInfo.connection = None
        accountInfo.onLineTime += time.time() - accountInfo.logInTime
        del self.accounts[accountInfo.accountName]
        for accInfo in self.accounts.values():
            accInfo.connection.sendMessage(accountInfo.accountName + ' quit the room\n')

    # def addConnector(self, conn):
    #     """
    #     add a connector to room
    #     :param conn: Connector
    #     :return:None
    #     :type conn: Connector
    #     """
    #     for co in self.connections:
    #         co.sendMessage(co.name + ' join the room')
    #     self.connections.add(conn)
    #     conn.sendMessage('system: welcome to join room( ' + self.name + ')! you can quit the room by enter "/quit"\n')
    #
    # def removeConnector(self, conn):
    #     """
    #     remove a connector
    #     :param conn: Connector
    #     :return:
    #     """
    #     self.connections.remove(conn)

    # def notifyAll(self, message):
    #     """
    #     notify all connector in the room
    #     :param message: str
    #     :return:
    #     """
    #     for conn in self.connections:
    #         conn.sendMessage(message)

    def empty(self):
        return len(self.connections) == 0

class Lobby(Room):

    def __init__(self, name = "Lobby"):
        """
        :param name: str
        :return:
        """
        Room.__init__(self,name)
        self.rooms = set()

    def addRoom(self, r):
        """

        :param r: Room
        :return:
        """
        self.rooms.add(r)
        self.notifyAll('system: a new room was built, welcome to jon, you can enter "/join '
                       + r.name + '" to join the new room\n')

    def removeRoom(self,r):
        self.rooms.remove(r)

    def addConnector(self, conn):
        Room.addConnector(self,conn)
        conn.sendMessage('system: you can use "/crate <roomname>" to create a new room\n')

class Cubby(Room):

    def __init__(self, name = 'Cubby'):
        Room.__init__(self, name)


class CommandParser(object):

    def beginWith(self, s, t):
        if(len(s) >= len(t) and s[0:len(t)] == t):
            return True
        else:
            return False


if __name__ == '__main__':
    userCount = {
        'netease1' : AccountInfo('netease1', '123'),
        'netease2' : AccountInfo('netease1', '123'),
        'netease3' : AccountInfo('netease1', '123'),
    }
    lobby = Lobby()
    logger = logConfig(True)
    gameServer = Accepter(config.SERVER_IP, config.SERVER_PORT)
    asyncore.loop()