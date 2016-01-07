__author__ = 'xiejun'

import select
import time



f = open('test.txt', 'w+')


while True:
    r, w, e = select.select([f.fileno()],[],[])
    time.sleep(1)
    print('xxx')