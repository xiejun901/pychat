__author__ = 'xiejun'

import time

class AccountInfo(object):

    def __init__(self, accountName, PassWord):
        self.accountName = accountName
        self.PassWord = PassWord
        self.onLineTime = 0
        self.connection = None
        self.logInTime = 0
        self.registerTime = time.time()
        self.room = None


