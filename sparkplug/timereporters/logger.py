"""
Sends timing information to the logs
"""

import logging
from sparkplug.logutils import LazyLogger
from sparkplug.timereporters.base import Base, _milliseconds


_log = LazyLogger(__name__)


class Logger(Base):
    def __init__(self, level="DEBUG"):
        super(Logger, self).__init__()
        # get the exact method for the correct logging level:
        self.logger = getattr(_log, str(level).lower())
        assert(callable(self.logger), "Logging level on timereporters.Logger does not resolve to anything useful")

    def append_exec(self, delta, tags=None):
        self.logger("OK: time {}, tags {}".format(delta, tags))

    def append_erro(self, delta, tags=None):
        self.logger("ERROR: time {}, tags {}".format(delta, tags))

    def append_wait(self, delta, tags=None):
        self.logger("WAIT TIME: time {}, tags {}".format(delta, tags))
