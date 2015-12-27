__author__ = 'xiejun'
import time

class Widget(object):

    def __init__(self, n):
        self.name = n

    def __hash__(self):
         return hash(self.name)

    def __cmp__(self, other):
        return self.name.__cmp__(other.name)

    def __eq__(self, other):
        return self.name.__eq__(other.name)



print time.time()