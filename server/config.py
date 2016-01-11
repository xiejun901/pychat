#!/usr/bin/python
# -*- coding: utf-8 -*-

import time

__author__ = 'xiejun'

# the server address
SERVER_IP = '0.0.0.0'

# the listen port
SERVER_PORT = 8080

# the parameter of the sock.listen()
MAX_LISTEN_NUM = 100

# the parameter of the recv lenght
MAX_RECV_LEN = 1024

# the seperator of the package
SEPRATOR = '\r\n'

# the parameter of the select
SELECT_TIME_OUT = 1

# the period of the 21 game, second
GAME21_PERIOD = 300

# the duaration time of the 21 game
GAME21_DUARATION = 120

# the first expires of the 21 game, if it set to None, the game will start after in one minute

GAME21_EXPIRES = time.time() + 120