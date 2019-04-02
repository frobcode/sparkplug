import threading
import time

from functools import wraps
from sparkplug.logutils import LazyLogger

_log = LazyLogger(__name__)
SLEEP_CONSTANT = 0.1

# reference: https://stackoverflow.com/questions/12435211/python-threading-timer-repeat-function-every-n-seconds
class _HeartbeatThread(threading.Thread):
    def __init__(self, connection, event_pause, event_end):
        threading.Thread.__init__(self)
        self._pause = event_pause
        self._end = event_end
        self._connection = connection
        self._interval = connection.heartbeat

    def run(self):
        _log.debug( "Heartbeat thread is launching")
        while not self._end.is_set():
            time.sleep( SLEEP_CONSTANT )
            while not self._pause.wait(max(0.1, self._interval)):
                _log.debug( "Sending heartbeat")
                try:
                    self._connection.send_heartbeat()
                except:
                    _log.debug( "Failed to send heartbeat.")
                    self._end.set()
                    break # while
        _log.debug( "Heartbeat thread is shutting down")


def _locked_call( lock, fn ):
    @wraps( fn )
    def locked_fn( *args, **kwargs ):
        with lock:
            r = fn( *args, **kwargs )
        return r
    return locked_fn


class Heartbeater( object ):
    """
    Context Manager

    Replaces the frame_writer on a connection
    for the purposes of sending asynchronous heartbeats.

    Also makes connection.transport _read() and _write() thread safe.

    This is particularly useful for consumers that take a very
    long time to process messages.
    """
    def __init__( self, connection ):
        connection.connect() # make sure we can access properties

        self._lock = threading.RLock()
        self._connection = connection

        self._holds = {}

        self._timer_pause = threading.Event()
        self._timer_pause.clear()
        self._timer_end = threading.Event()
        self._timer_end.clear()
        self._timer = None
        if connection.heartbeat:
            self.new_timer()

    def new_timer( self ):
        if self._timer :
            paused = self._timer_pause.is_set() # push state
            # set events so thread ends:
            self._timer_pause.set()
            self._timer_end.set()
            self._timer.join()
            if not paused:
                self._timer_pause.clear() # pop state
        self._timer_end.clear()
        self._timer = _HeartbeatThread( self._connection, self._timer_pause, self._timer_end )
        self._timer.start()

    def check_timer( self ):
        if self._timer_end.is_set() :
            self.new_timer()

    def __enter__(self):
        _log.debug( "Entering heartbeat context")
        self._timer_pause.clear()
        if self._timer:
            self.check_timer()
            _log.debug( "Connection frame_writer is serialized")
            self._holds[ 'frame_writer']  = self._connection.frame_writer
            self._connection.frame_writer = self
            self._holds[ 'transport._read' ] = self._connection.transport._read
            self._connection.transport._read = _locked_call( self._lock, self._connection.transport._read )
            self._holds[ 'transport._write' ] = self._connection.transport._write
            self._connection.transport._write = _locked_call( self._lock, self._connection.transport._write )

    def __call__( self, *args ):
        # all writes on connection will be serialized
        if self._timer:
            self.check_timer()
        with self._lock:
            self._holds[ 'frame_writer' ]( *args )

    def __exit__( self ):
        self._timer_pause.set()
        if self._timer:
            self._connection.frame_writer = self._holds[ 'frame_writer' ]
            self._connection.transport._read = self._holds[ 'transport._read' ]
            self._connection.transport._write = self.holds[ 'transport._write' ]
            self._holds.clear()
        _log.debug( "Leaving heartbeat context")

    def teardown( self ):
        self._timer_pause.set()
        self._timer_end.set()
        if self._timer:
            self._timer.join()
            self._timer = None
