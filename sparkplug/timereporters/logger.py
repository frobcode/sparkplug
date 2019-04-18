"""
Sends timing information to the logs
"""

import logging
from sparkplug.logutils import LazyLogger
import sparkplug.timereporters.base

_log = LazyLogger(__name__)

class Logger( sparkplug.timereporters.base.Base ):
    def __init__(self, aggregation_count, level="DEBUG" ):
        super().__init__(aggregation_count)
        self.exec = []
        self.erro = []
        self.wait = []
        # get the exact method for the correct logging level:
        self.logger = getattr( _log, str(level).lower() )
        assert( callable(self.logger), "Logging level on timereporters.Logger does not resolve to anything useful" )

    def append_exec( self, delta ):
        self.exec.append( delta )
        if len( self.exec ) >= self.aggregation_count :
            mn, md, mx = sparkplug.timereporters.base.mn_md_mx( self.exec )
            del self.exec[:]
            self.logger( "msg exec (min med max) ms: {:0.2f} {:0.2f} {:0.2f}".format( mn, md, mx ))

    def append_erro( self, delta ):
        self.erro.append( delta )
        if len( self.erro ) >= self.aggregation_count :
            mn, md, mx = sparkplug.timereporters.base.mn_md_mx( self.erro )
            del self.erro[:]
            self.logger( "msg erro (min med max) ms: {:0.2f} {:0.2f} {:0.2f}".format( mn, md, mx ))

    def append_wait( self, delta ):
        self.wait.append( delta )
        if len( self.wait ) >= self.aggregation_count :
            mn, md, mx = sparkplug.timereporters.base.mn_md_mx( self.wait )
            del self.wait[:]
            self.logger( "msg wait (min med max) ms: {:0.2f} {:0.2f} {:0.2f}".format( mn, md, mx ))
