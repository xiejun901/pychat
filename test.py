__author__ = 'xiejun'
import time
import sqlite3

class Widget(object):

    def __init__(self, n):
        self.name = n

    def __hash__(self):
         return hash(self.name)

    def __cmp__(self, other):
        return self.name.__cmp__(other.name)

    def __eq__(self, other):
        return self.name.__eq__(other.name)



# conn = sqlite3.connect('test.db')
# cursor = conn.cursor()
# cursor.execute('CREATE TABLE user(id varchar(20) primary key, name varchar(20))')
# cursor.execute('insert into user (id, name) values (\'1\', \'Michael\')')
# print cursor.rowcount

# import select
# import socket
#
# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.bind(('localhost',8080))
# s.listen(10)
# p = select.epoll()
# p.register(s.fileno(), select.EPOLLIN)
# print select.EPOLLOUT
# print select.EPOLLIN
# print select.EPOLLERR
# while True:
#     epoll_list = p.poll()
#     for fileno, mask in epoll_list:
#         if mask == select.EPOLLIN:
#             if fileno == s.fileno():
#                 sock, addr = s.accept()
#                 p.register(sock.fileno(), select.EPOLLOUT | select.EPOLLIN)
#         elif mask == select.EPOLLOUT:
#             print "epoll_out"

# username = 'xiejun'
# sql = 'SELECT password FROM userInfo WHERE username = %s ' % ('"'+username+'"')
# print sql

import random
import re
# s  = '1+1+5+7'
# patter = '\D'
# numbers = [int(i) for i in re.split(patter, s)]
# print numbers
#
# try:
#     ans = eval(s)
# except Exception, e:
#     print repr(e)
from operator import itemgetter
l = [(10, 1 ),(9, 2), (11, 3), (10,4)]
print sorted(l, key= itemgetter(0), reverse= True)