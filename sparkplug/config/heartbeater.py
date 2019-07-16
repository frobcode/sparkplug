import threading
import time
import traceback

from sparkplug.logutils import LazyLogger

_log = LazyLogger(__name__)


# reference: https://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds
class _HeartbeatThread(threading.Thread):
    """
    This thread sends heartbeats at periodic intervals
    It has events for pausing heartbeats and
    for completely shutting down, which can be used
    by external entities.
    """

    def __init__(self, connection, event_pause, event_end):
        threading.Thread.__init__(self)
        self._pause = event_pause
        self._end = event_end
        self._connection = connection
        assert(connection.heartbeat)
        self._interval = max(0.1, connection.heartbeat * 0.4)

    def run(self):
        _log.debug("Heartbeat thread is launching")
        while not self._end.is_set():
            try:
                # Theading.Event.wait() is EXTREMELY SLOW, ~100ms
                # use sleep() instead, then check the state of pause after:
                time.sleep(self._interval)
                if not self._pause.is_set():
                    _log.debug("Send heartbeat")
                    self._connection.send_heartbeat()
            except Exception:
                _log.error(traceback.format_exc())
                _log.debug("Failed to send heartbeat")
                self._end.set()
        _log.debug("Heartbeat thread is shutting down")


class Heartbeater(object):
    """
    Context Manager
    In the scope of its context, the heartbeat thread
    will send heartbeats.

    Don't forget to call teardown() when you are finished.
    """

    def __init__(self, connection):
        self._connection = connection

        self._timer_pause = threading.Event()
        self._timer_pause.set()
        self._timer_end = threading.Event()
        self._timer_end.clear()
        self._timer = None
        if connection.heartbeat:
            self.start_new_timer()

    def start_new_timer(self):
        if self._timer:
            paused = self._timer_pause.is_set()  # push state
            # set events so thread ends:
            self._timer_pause.set()
            self._timer_end.set()
            self._timer.join()
            if not paused:
                self._timer_pause.clear()  # pop state
        self._timer_end.clear()
        self._timer = _HeartbeatThread(self._connection, self._timer_pause, self._timer_end)
        self._timer.start()

    def clear_timer_end(self):
        if self._timer_end.is_set():
            self.start_new_timer()

    def __enter__(self):
        if self._timer:
            self._timer_pause.clear()
            self.clear_timer_end()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if self._timer:
            self._timer_pause.set()
        return False

    def teardown(self):
        self._timer_pause.set()
        self._timer_end.set()
        if self._timer:
            self._timer.join()
            self._timer = None

    def __del__(self):
        self.teardown()
