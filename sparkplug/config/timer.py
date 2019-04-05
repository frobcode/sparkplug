
import datetime
from sparkplug.logutils import LazyLogger

_log = LazyLogger(__name__)

##################################################

def _milliseconds( timedelta ):
    return timedelta / datetime.timedelta( microseconds=1000 )

##################################################

def _mn_md_mx( l ):
    "calculate min median max from a list of timedeltas"
    mn = 0
    median = 0
    mx = 0
    if l :
        lenl = len(l)
        ordered = sorted( l )
        mn = _milliseconds( ordered[0] )
        mx = _milliseconds( ordered[-1] )
        if lenl & 0x01 :
            # odd number of samples
            median = _milliseconds( ordered[ lenl >> 1 ] )
        else:
            # even number of samples
            median = 0.5 * _milliseconds( ordered[ lenl >> 1 ] + ordered[ ( lenl >> 1 ) - 1 ])
    return( mn, median, mx )

##################################################

class Timer( object ):
    def __init__( self, callback, threshold=10 ):
        self._execs = []
        self._waits = []
        self._callback = callback
        self._threshold = int( threshold )


    @staticmethod
    def _log_stats( kind, l ):
        mn, md, mx = _mn_md_mx( l )
        _log.info( "msg {} time (min,med,max) ms: {:0.2f} {:0.2f} {:0.2f}".format( kind, mn, md, mx ))
        return


    def __call__( self, msg ):
        try:
            start_time = datetime.datetime.now()
            if hasattr( msg, "timestamp" ) and isinstance( msg.timestamp, datetime.datetime ):
                self._waits.append( start_time - msg.timestamp )

            ret = self._callback( msg )
        finally:
            self._execs.append( datetime.datetime.now() - start_time )
            if len( self._execs ) >= self._threshold:
                self._log_stats( "wait", self._waits )
                del self._waits[:]
                self._log_stats( "exec", self._execs )
                del self._execs[:]

        return ret
