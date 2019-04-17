import datetime

##################################################

def _milliseconds( timedelta ):
    return timedelta / datetime.timedelta( microseconds=1000 )


##################################################

def mn_md_mx( l ):
    "calculate min median max from a list of timedeltas, returns the time in milliseconds"
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

class Base( object ):
    def __init__(self, aggregation_count ):
        self.aggregation_count = aggregation_count

    def append_wait( self, delta ):
        pass

    def append_exec( self, delta ):
        pass

    def append_erro( self, delta ):
        pass
