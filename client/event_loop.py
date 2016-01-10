__author__ = 'xiejun'
import select
import time
import errno

class EventLoop(object):
    """
    use select.select
    """

    def __init__(self):
        self.map = {}
        self.quit = False
        self.available_timers = []

    def add_event(self, event):
        self.map[event.fileno] = event

    def remove_event(self, event):
        del self.map[event.fileno]

    def add_timer(self, timer):
        self.available_timers.append(timer)

    def loop(self, timeout = 1):
        while not self.quit:
            r = []
            w = []
            e = []
            for fileno, obj in self.map.items():
                if(obj.readable()):
                    r.append(fileno)
                if(obj.writable()):
                    w.append(fileno)
                if(obj.exptable()):
                    e.append(fileno)
            try:
                r, w, e = select.select(r, w, e, timeout)
            except select.error, err:
                if err[0] != errno.EINTR:
                    raise
                else:
                    continue
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
            self.update_timer(current)


    def update_timer(self, current):
        # process all timers
        for timer in self.available_timers:
            while current > timer.expires:
                timer.callback(current)
                timer.expires += timer.period



class Event(object):

    def __init__(self, fileno = -1):
        self.fileno = fileno

    def writable(self):
        return False

    def readable(self):
        return False

    def exptable(self):
        return False

    def handle_write_event(self):
        pass

    def handle_read_event(self):
        pass

    def handle_expt_event(self):
        pass


class TaskTimer(object):
    # base class of timer
    def __init__(self, _expires, _period):
        """
        :param _expires: expires tiem
        :param _period: timer period
        :return:
        """
        self.expires = _expires
        self.period = _period

    def callback(self, current):
        """
        timer call back, often need to be override
        :param current:
        :return:
        """
        print('timer happens in' + time.strftime('%d-%b-%Y %H:%M:%S ', time.localtime(current) ))