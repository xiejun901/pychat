__author__ = 'xiejun'

class Widget(object):

    def __init__(self, n):
        self.name = n

    def __hash__(self):
         return hash(self.name)

    def __cmp__(self, other):
        return self.name.__cmp__(other.name)

    def __eq__(self, other):
        return self.name.__eq__(other.name)



w1 = Widget('xiejun')
w2 = Widget('zhuwne')
w3 = Widget('xiejun')

print w1 == w2

m = {}
m[w1] = 1
m[w2] = 2
m[w3] = 3
print(m)