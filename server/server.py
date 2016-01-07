__author__ = 'xiejun'
import socket
import select
import config
import logging
from userInfomation import user_info_db
import time
import random
import re
from operator import itemgetter
import thread

connectors = {}

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

logger = logConfig(True)

class Connector(object):

    def __init__(self, sock, loop):
        self.sock = sock
        self.fileno = sock.fileno()
        self.loop = loop
        self.obuffer = ""
        self.ibuffer = []
        # record the username and mask is this connection has sign in
        self.name = None

    def handle_read_event(self):
        data =  self.sock.recv(1024)
        if not data:
            self.close()
        sep_loc = data.find(config.SEPRATOR)
        if sep_loc >= 0 :
            message = ''.join(self.ibuffer)
            message += (data[:sep_loc])
            self.ibuffer.append(data[sep_loc+len(config.SEPRATOR):])
            self.process_message(message)
        else:
            self.ibuffer.append(data)

    def handle_write_event(self):
        sent = self.sock.send(self.obuffer)
        self.obuffer = self.obuffer[sent:]

    def handle_expt_event(self):
        logger.info("handle expt event")

    def readable(self):
        return True

    def writable(self):
        return len(self.obuffer) > 0

    def close(self):
        logger.info("close connector %s", repr(self.sock.getpeername()))
        del self.loop.map[self.fileno]
        self.sock.close()

    def process_message(self, message):
        if self.begin_with(message, '/SIGNUP'):
            self.sign_up(message)
        elif self.begin_with(message, '/SIGNIN'):
            self.sign_in(message)
        elif self.begin_with(message, '/SIGNOUT'):
            self.sign_out()
        elif self.begin_with(message, '/21GAME'):
            available_timers[0].process_answer_callback(message, self.name)
        else:
            for _, connector in connectors.items():
                connector.send_message(self.name + ': ' + message)

    def begin_with(self, s, t):
        if len(t) > len(s):
            return False
        if s[:len(t)] == t:
            return True
        return False

    def send_message(self, message):
        self.obuffer += time.strftime("%d %b %Y %H:%M:%S", time.localtime())
        self.obuffer += '\n'
        self.obuffer += message
        self.obuffer += '\n'

    def sign_out(self):
        if(not self.has_sign_in()):
            self.send_message("system: you can't sign out before you sign in.")
            return
        del connectors[self.name]
        for _, connector in connectors.items():
            connector.send_message('system:' + self.name + ' quit!')
        self.send_message('system: ' + self.name + ' bye bye!')
        user_info_db.sign_out_user(self.name)
        self.name = None

    def sign_in(self, message):
        if(self.has_sign_in()):
            self.send_message("system: can't sign in repeatedly.")
            return
        li = message.split(' ', 2)
        if (len(li)!=3):
            self.send_message('system: wrong account or password.')
            return
        _, username, password = li
        if(self.has_sign_in(username)):
            self.send_message("system: can't sign in repeatedly.")
            return
        if(user_info_db.sign_in_user(username,password)):
            self.name = username
            for _, connector in connectors.items():
                connector.send_message('system: ' + self.name + ' join the room!')
            connectors[username] = self
            self.send_message('system: welcome, ' + self.name )
        else:
            self.send_message('system: wrong account or password.')

    def sign_up(self, message):
        # register a new account
        li = message.split(' ', 2)
        if (len(li) != 3 or len(li[1]) > 20 or len(li[2]) > 20):
            self.send_message('system: the correct format to register a new account is "/SIGNUP username password", '
                              'username and passwrod should less than 20 characters, your input is wrong.')
            return
        username = li[1]
        password = li[2]
        if (user_info_db.is_exist_user(username)):
            self.send_message('system: the username is exist, please input another one.')
            return
        if(user_info_db.sign_up_user(username, password)):
            self.send_message('system: register successfully.')
        else:
            self.send_message('system: register failed, try again.')

    def has_sign_in(self, name = None):
        #has some account sign in through this connection
        if name is not None:
            return name in connectors
        return self.name is not None



class Accpter(object):

    def __init__(self, sock, loop):
        self.sock = sock
        self.fileno = sock.fileno()
        self.loop = loop

    def handle_read_event(self):
        connection, addr = self.sock.accept()
        connection.setblocking(0)
        connector = Connector(connection, self.loop)
        self.loop.add_event(connector)
        logger.info("new connection %s", repr(addr))

    def handle_write_event(self):
        pass

    def handle_expt_event(self):
        pass

    def readable(self):
        return True

    def writable(self):
        return False

class EventLoop(object):
    """
    use select.select
    """

    def __init__(self):
        self.map = {}
        self.quit = False

    def add_event(self, chanel):
        self.map[chanel.fileno] = chanel

    def loop(self):
        while not self.quit:
            r = []
            w = []
            e = []
            for fileno, obj in self.map.items():
                if(obj.readable()):
                    r.append(fileno)
                if(obj.writable()):
                    w.append(fileno)
                if(obj.writable() and obj.readable):
                    e.append(fileno)
            r, w, e = select.select(r, w, e, config.SELECT_TIME_OUT)
            for fileno in r:
                obj = self.map.get(fileno)
                if obj is None:
                    continue
                obj.handle_read_event()
            for fileno in w:
                obj = self.map.get(fileno)
                if obj is None:
                    continue
                obj.handle_write_event()
            for fileno in e:
                obj = self.map.get(fileno)
                if obj is None:
                    continue
                obj.handle_expt_event()
            current = time.time()
            update_timer(current)

#available timer task
available_timers = []

def update_timer(current):
    for timer in available_timers:
        while current > timer.expires:
            timer.callback(current)
            timer.expires += timer.period



class TaskTimer(object):

    def __init__(self, _expires, _period):
        self.expires = _expires
        self.period = _period

    def callback(self, current):
        print('timer happens in' + time.strftime('%d-%b-%Y %H:%M:%S ', time.localtime(current) ))


class Game21Timer(TaskTimer):

    def __init__(self, _expires, _period, _duaration):
        TaskTimer.__init__(self, _expires, _duaration)
        self.numbers = []
        self.game_in = False
        self.game_start_time = _expires
        self.game_end_time = _expires + _duaration
        self.game_period = _period
        self.game_duaration = _duaration
        self.patter = '\D+'
        self.answers = []



    def callback(self, current):
        if current > self.game_start_time:
            # game not start, start a game
            logger.info( 'game start')
            self.game_start_time += self.game_period
            self.game_start()
        elif current > self.game_end_time:
            # time up
            logger.info( "game time up")
            # update the next time up
            self.game_end_time = self.game_start_time + self.game_duaration
            if not self.game_in:
                # game has end by right answer, do nothing
                pass
            else:
                # time up and no right answer, find the earliest and largest answer
                self.game_in = False
                if len(self.answers) == 0:
                    for _, connector in connectors.items():
                        connector.send_message('system: no person answer the question, game over')
                    return
                rank = sorted(self.answers, key=itemgetter(0), reverse= True)
                self.winner = rank[0][1]
                for _, connector in connectors.items():
                    connector.send_message('system: ' + self.winner + ' win the game, his answer is ' + rank[0][2])


        else:
            # recently game is in
            pass

    def game_start(self):
        self.winner = None
        self.answers = []
        self.game_in = True
        random.seed()
        self.numbers = [random.randint(1,10) for i in range(4)]
        self.numbers.sort()
        message = '''
system: The 21 game will start, you should use the following four numbers, +, -, *, /, and parenthesis to make the
result of the expression is 21, if it can't be equal to 21, the largest number will win
the four numbers are: %d   %d   %d   %d
you can use /21GAME <expression> to answer this question
''' %(self.numbers[0], self.numbers[1], self.numbers[2], self.numbers[3])
        for _, connector in connectors.iteritems():
            connector.send_message(message)


    def process_answer_callback(self, message, username):
        li = message.split(' ', 1)
        conn = connectors.get(username)
        if conn is None:
            logger("can't find username in connectors")
            return
        if len(li) != 2:
            conn.send_message('system: you should input your answer by format of "/21GAME <expression>"')
            return
        if not self.game_in:
            conn.send_message('system: there is no game in, the next game will start at ' + time.strftime('%d-%b-%Y %H:%M:%S ', time.localtime(self.expires)))
            return
        expression = li[1]
        numbers =[int(i) for i in re.split(self.patter, expression)]
        numbers.sort()
        if(self.numbers != numbers):
            conn.send_message('system: wrong input, the four number are: %d   %d   %d   %d' %(self.numbers[0], self.numbers[1], self.numbers[2], self.numbers[3]))
        try:
            ans = eval(expression)
            if ans ==21:
                # right answer
                self.game_in = False
                self.winner = username
                for _, connector in connectors.items():
                    connector.send_message('system: ' + self.winner + ' win the game, game over. his answer is: ' + expression)
            else:
                # not right answer, store it
                self.answers.append((ans, username, expression))
        except Exception, e:
            conn.send_message('system: wrong input, the error is %s' %repr(e))


def game_end_control(tseconds, obj):
    # to cotrol the game duaration
    time.sleep(tseconds)
    obj.game_in = False


def main():
    logger.info('server start!')
    loop = EventLoop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((config.SERVER_IP, config.SERVER_PORT))
    sock.listen(10)
    sock.setblocking(0)
    accepter = Accpter(sock, loop)
    loop.add_event(accepter)
    game_timer = Game21Timer(time.time(), 120, 40)
    available_timers.append(game_timer)
    try:
        loop.loop()
    finally:
        sock.close()






# def main():
#     logger = logConfig(True)
#     socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     socket_server.bind((config.serverip, config.serverport))
#     socket_server.listen(1)
#     socket_server.setblocking(0)
#
#     epollfd = select.epoll()
#     epollfd.register(socket_server.fileno(), select.EPOLLIN)
#
#     message_queues = {}
#     connections = {}
#     connections[socket_server.fileno()] = socket_server
#     try:
#         while True:
#             events = epollfd.poll()
#             for fd, event in events:
#                 socket_event = connections[fd]
#                 if event == select.POLLIN:
#                     if socket_event == socket_server:
#                         # new connection
#                         connection, addr = socket_server.accept()
#                         logger.info('new connection from %s', repr(addr))
#                         connection.setblocking(0)
#                         connections[connection.fileno()] = connection
#                         message_queues[connection.fileno()] = []
#                         epollfd.register(connection.fileno(), select.POLLIN)
#                     else:
#                         data = socket_event.recv(config.MAX_RECV_LEN)
#                         logger.info('recieve data: %s', repr(data))
#                         if data:
#                             message_queues[socket_event.fileno()].append(data)
#                             epollfd.modify(fd, select.EPOLLOUT)
#                         else:
#                             epollfd.modify(fd, select.EPOLLOUT)
#                 elif event == select.POLLOUT:
#                     # writtable
#                     logger.info('event write')
#                     msg = ''.join(message_queues[socket_event.fileno()])
#                     if len(msg) == 0:
#                         socket_event.close()
#                     socket_event.send(msg)
#                     epollfd.modify(fd, select.EPOLLIN)
#                 elif event == select.EPOLLHUP:
#                     epollfd.unregister(fd)
#                     connections[fd].close()
#                     del connections[fd]
#     finally:
#         epollfd.unregister(socket_server.fileno())
#         epollfd.close()
#         socket_server.close()


if __name__ == '__main__':
    main()

