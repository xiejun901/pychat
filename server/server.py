#!/usr/bin/python
# -*- coding: utf-8 -*-

__author__ = 'xiejun'
import socket
import logging
import time
import random
import re
from operator import itemgetter
import errno

import config
from user_infomation import user_info_db
import event_loop


def log_config(on_terminal):
    #config the logger
    FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
    logging.basicConfig(level=logging.DEBUG,format=FORMAT, filename="server.log", filemode='w+')
    logger = logging.getLogger("server_log")
    if on_terminal is True:
        # control need to print log on terminal
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        console.setFormatter(formatter),
        logger.addHandler(console)
    return logger


class Connector(event_loop.Event):

    def __init__(self, sock, loop):
        self.sock = sock
        self.fileno = sock.fileno()
        self.loop = loop
        self.obuffer = ""
        self.ibuffer = []
        # record the username and mask is this connection has sign in
        self.name = None
        self.heart_beat_cnt = 0

        self.help_message = 'system: you input a error command, the usages are follows:\n' \
                            '\n' \
                            '/SIGNIN username password               sign in by your username and password\n' \
                            '/SIGNUP username password               register a new username and password\n' \
                            '/SIGNOUT                                sign out\n' \
                            '/W username                             send message to other people by whisper\n' \
                            '/CREATEROOM roomname                    create a new room and join in\n' \
                            '/JOINROOM roomname                      join a room\n' \
                            '/QUITROOM                               quit room\n' \
                            '/CHATROOM                               send message to room\n' \
                            '/21GAME expression                      answer the 21 game\n' \
                            '/GETONLINETIME                          get you online time\n'

    def handle_read_event(self):
        try:
            data = self.sock.recv(1024)
        except socket.error, err:
            if err[0] != errno.ECONNRESET:
                raise
            else:
                logger.warning('recieve a RST')
                self.sign_out()
                self.close()
            return
        if not data:
            self.sign_out()
            self.close()
            return
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
        try:
            data = self.sock.recv(1, socket.MSG_OOB)
        except socket.error, err:
            if(err[0] != errno.EWOULDBLOCK):
                logger.warning('sock.recv(1, socket.MSG_OOB) get bad error')
                return
        self.sock.send('c', socket.MSG_OOB)
        self.heart_beat_cnt = 0

    def readable(self):
        return True



    def writable(self):
        return len(self.obuffer) > 0

    def exptable(self):
        return True

    def close(self):
        logger.info("close connector")
        del self.loop.map[self.fileno]
        self.sock.close()

    def process_message(self, message):
        if self.begin_with(message, '/SIGNUP '):
            self.sign_up(message)
        elif self.begin_with(message, '/SIGNIN '):
            self.sign_in(message)
        elif self.begin_with(message, '/SIGNOUT'):
            self.sign_out()
        elif self.begin_with(message, '/W '):
            # chat to someone
            self.chat_to_someone(message)
        elif self.begin_with(message, '/CREATEROOM '):
            # create a new room
            self.create_new_room(message)
        elif self.begin_with(message, '/QUITROOM'):
            # quit the room
            self.quit_room(message)
        elif self.begin_with(message, '/JOINROOM '):
            # join a room
            self.join_room(message)
        elif self.begin_with(message, '/CHATROOM '):
            # chat to room
            self.chat_to_room(message)
        elif self.begin_with(message, '/21GAME '):
            self.game21_process_message(message)
        elif self.begin_with(message, '/GETONLINETIME'):
            self.get_online_time(message)
        elif self.begin_with(message, '/'):
            self.send_message(self.help_message)
        else:
            self.send_to_all(message)

    def begin_with(self, s, t):
        if len(t) > len(s):
            return False
        if s[:len(t)] == t:
            return True
        return False

    def send_message(self, message):
        _message = time.strftime("\n%d %b %Y %H:%M:%S", time.localtime()) + '\n' + message + '\n\n'
        self.obuffer += _message

    def sign_out(self):
        if(not self.has_sign_in()):
            self.send_message("system: you can't sign out before you sign in.")
            return
        del connectors[self.name]
        for _, connector in connectors.items():
            connector.send_message('system:' + self.name + ' quit!')
        self.send_message('system: ' + self.name + ' bye bye!')
        user_info_db.update_online_time(self.name)
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

    def chat_to_someone(self, message):
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        li = message.split(' ', 2)
        if(len(li) != 3):
            self.send_message('system: the format of send message to player is: /M username message')
            return
        othername = li[1]
        contents = li[2]
        other_conn = connectors.get(othername)
        if other_conn is None:
            self.send_message('system: the playser you send message to was offline')
            return
        other_conn.send_message(self.name + ': ' + contents)

    def create_new_room(self, message):
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        li = message.split(' ', 1)
        if (len(li) != 2):
            self.send_message('system: the format of create new room is: /CREATEROOM roomname')
            return
        room_name = li[1]
        if rooms.get(room_name) is not None:
            self.send_message('system: the room has exist, you join the room by: /JOINROOM roomname')
            return
        rooms[room_name] = Room(room_name)
        rooms[room_name].add_user(self.name)
        self.send_message('you have create a new room and join the room')

    def quit_room(self, message):
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        if(message != '/QUITROOM'):
            self.send_message('system: command error')
            return
        room = username_to_room.get(self.name)
        if room is None:
            self.send_message('system: you are not in any room')
            return
        room.remove_user(self.name)
        room.send_message_to_all('system: '+ self.name +' quit the room')

    def join_room(self, message):
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        li = message.split(' ', 1)
        if(len(li) != 2):
            self.send_message('system: command error')
            return
        room_name = li[1]
        room = rooms.get(room_name)
        if room is None:
            self.send_message('system: room is not exists, you can creat the room by command: /CRATEROOM roomname')
            return
        room.send_message_to_all('system: '+ self.name +' join the room')
        room.add_user(self.name)

    def chat_to_room(self, message):
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        li = message.split(' ', 1)
        if (len(li) != 2):
            self.send_message('system: command error')
            return
        content = li[1]
        room = username_to_room.get(self.name)
        if room is None:
            self.send_message('system: you are not in any room, please join a room first')
            return
        room.send_message_to_all(self.name +': ' + content)


    def has_sign_in(self, name = None):
        #has some account sign in through this connection
        if name is not None:
            return name in connectors
        return self.name is not None

    def game21_process_message(self, message):
        # process 21 game message
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        li = message.split(' ', 1)
        if len(li) != 2:
            self.send_message('system: command error')
            return
        game21.process_answer(li[1], self, self.name)

    def get_online_time(self, message):
        # get online time
        if not self.has_sign_in():
            self.send_message('system: please sign in first')
            return
        ot = user_info_db.get_online_time(self.name)
        self.send_message('system: you online time is %d seconds.' %ot)

    def send_to_all(self, message):
        if(not self.has_sign_in()):
            self.send_message('system: please sign in first')
            return
        for _, connector in connectors.items():
                connector.send_message(self.name + ': ' + message)

    def check_heart_beat(self, heart_beat_max):
        self.heart_beat_cnt += 1
        if (self.heart_beat_cnt > heart_beat_max):
            self.sign_out()
            self.close()



class Accpter(event_loop.Event):

    def __init__(self, host, port, loop):
        self.loop = loop
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.fileno = self.sock.fileno()
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        self.sock.bind((host, port))
        self.sock.listen(config.MAX_LISTEN_NUM)

    def handle_read_event(self):
        connection, addr = self.sock.accept()
        connection.setblocking(0)
        connector = Connector(connection, self.loop)
        self.loop.add_event(connector)
        logger.info("new connection %s", repr(addr))

    def readable(self):
        return True

    def writable(self):
        return False

    def exptable(self):
        return True

    def close(self):
        self.sock.close()
        self.loop.remove_event(self)


class Game21Timer(event_loop.TaskTimer):
    """
    the 21 game timer task
    """

    def __init__(self, _expires, _period, _duaration, timer_timeout):
        event_loop.TaskTimer.__init__(self, _expires, _period)
        self.game_duaration = _duaration
        self.timer_timeout = timer_timeout

    def callback(self, current):
        logger.info( 'game start')
        game21.game_start()
        # reset the timer to control time out
        self.timer_timeout.reset_timer(self.expires + self.game_duaration)


class Game21(object):

    def __init__(self):
        random.seed()
        self.numbers = [random.randint(1,9) for i in range(4)]
        self.numbers.sort()
        self.game_in = True
        self.patter = '\D+'
        self.answers = []
        self.answered_username = set()
        self.winner = None

    def process_answer(self, expression, conn, username):
        if (self.check_message(expression, conn, username)):
            try:
                ans = eval(expression)
                if ans == 21:
                    # right answer
                    self.game_in = False
                    self.winner = username
                    for _, connector in connectors.items():
                        connector.send_message('system: ' + self.winner + ' win the game, game over. his answer is: ' + expression)
                elif ans > 21:
                    # if the answer over 21, it will be treat as bad ansert
                    self.answered_username.add(username)
                else:
                    # not right answer, store it
                    self.answers.append((ans, username, expression))
                    self.answered_username.add(username)
            except Exception, e:
                conn.send_message('system: wrong input, the error is %s' %repr(e))

    def check_message(self, expression, conn, username):
        if not self.game_in:
            conn.send_message('system: there is no game in, the next game will start at '
                              + time.strftime('%d-%b-%Y %H:%M:%S ', time.localtime(self.expires)))
            return False
        numbers =[int(i) for i in re.split(self.patter, expression) if i != '' ]
        numbers.sort()
        if(self.numbers != numbers):
            conn.send_message('system: wrong input, the four number are: %d   %d   %d   %d' %(self.numbers[0], self.numbers[1], self.numbers[2], self.numbers[3]))
            return False
        for ch in expression:
            # check if contains operator other than + - * /
            if not (ch.isdigit() or (ch in '+-*/()') ):
                conn.send_message('system: wrong input, the right fromat samples: /21GAME 1+2/3*4')
                return False
        return True

    def game_time_out(self):
        # time out and no anaser are equal to 21
        logger.info( "game time up")
        if not self.game_in:
            return
        self.game_in = False
        if len(self.answers) == 0:
            for _, connector in connectors.items():
                connector.send_message('system: no person answer the question, game over')
            return
        rank = sorted(self.answers, key=itemgetter(0), reverse= True)
        self.winner = rank[0][1]
        for _, connector in connectors.items():
            connector.send_message('system: ' + self.winner + ' win the game, his answer is ' + rank[0][2])

    def game_start(self):
        self.winner = None
        self.answers = []
        self.game_in = True
        random.seed()
        self.numbers = [random.randint(1,9) for i in range(4)]
        self.numbers.sort()
        message = "system: The 21 game will start, you should use the following four numbers, +, -, *, /, " \
                  "and parenthesis to make the result of the expression is 21," \
                  " if it can't be equal to 21, the largest number less than 21 will win game. \n " \
                  "the four numbers are: %d   %d   %d   %d \n " \
                  "you can use /21GAME <expression> to answer this question" \
                  %(self.numbers[0], self.numbers[1], self.numbers[2], self.numbers[3])
        for _, connector in connectors.iteritems():
            connector.send_message(message)


class Room(object):

    def __init__(self, roomname):
        self.users = set()
        self.roomname = roomname
        self.user_nums = 0

    def add_user(self, username):
        self.users.add(username)
        username_to_room[username] = self
        self.user_nums += 1

    def remove_user(self, username):
        self.users.remove(username)
        del username_to_room[username]
        self.user_nums -= 1
        if self.user_nums == 0:
            # no user in thr romm, delete it
            del rooms[self.room_name]

    def send_message_to_all(self, message):
        for username in self.users:
            conn = connectors.get(username)
            if conn is not None:
                conn.send_message(message)


class HeartBeat(event_loop.TaskTimer):

    def __init__(self, expires, period, heart_beat_max):
        event_loop.TaskTimer.__init__(self, expires, period)
        self.heart_beat_max = heart_beat_max

    def callback(self, current):
        for _, connector in connectors.items():
            connector.check_heart_beat(self.heart_beat_max)

class Game21TimeOutTimer(event_loop.TaskTimer2):

    def __init__(self, _expires):
        event_loop.TaskTimer2.__init__(self, _expires)

    def callback(self, current):
        game21.game_time_out()

# rooms
rooms = {}

# 21 game
game21 = Game21()

# stroe the connections, name: connector
connectors = {}

#available timer task, store the timers
available_timers = []

# relationship of username and room
username_to_room = {}

# the logger
logger = log_config(True)

def main():
    logger.info('server start!')
    loop = event_loop.EventLoop()
    accepter = Accpter(config.SERVER_IP, config.SERVER_PORT, loop)
    loop.add_event(accepter)
    first_expires = config.GAME21_EXPIRES
    if first_expires is None:
        t = time.localtime()
        t2 = time.struct_time((t.tm_year,
                              t.tm_mon,
                              t.tm_mday,
                              t.tm_hour+1,
                              0,
                              0,
                              t.tm_wday,
                              t.tm_yday,
                              t.tm_isdst
        ))
        first_expires = time.mktime(t2)
    # add timer to control 21 game time out
    game_time_out_timer = Game21TimeOutTimer(0)
    loop.add_timer(game_time_out_timer)
    # add 21 game timer to event loop
    game_timer = Game21Timer(first_expires, config.GAME21_PERIOD, config.GAME21_DUARATION, game_time_out_timer)
    loop.add_timer(game_timer)
    # add heart beat timer to event loop
    heart_beat_timer = HeartBeat(time.time(), 3, 10)
    loop.add_timer(heart_beat_timer)
    try:
        # start the event loop
        loop.loop(config.SELECT_TIME_OUT)
    finally:
        accepter.close()

if __name__ == '__main__':
    main()

