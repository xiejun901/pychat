__author__ = 'xiejun'
import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('localhost', 8080))
sock.listen(5)
conn, addr = sock.accept()
conn.send('sssssss')
time.sleep(10)