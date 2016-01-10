__author__ = 'xiejun'


import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 8080))
time.sleep(1)
sock.close()