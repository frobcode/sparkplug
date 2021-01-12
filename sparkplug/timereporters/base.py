import datetime


def _milliseconds(timedelta):
    return timedelta.total_seconds() * 1000


class Base(object):
    def __init__(self):
        pass

    def append_wait(self, delta, tags=None):
        pass

    def append_exec(self, delta, tags=None):
        pass

    def append_erro(self, delta, tags=None):
        pass
