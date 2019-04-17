"""
Sends timing information to Datadog custom metrics
Uses a thread to send at regular intervals, without
interfering with the main consumer thread
"""

from sparkplug.logutils import LazyLogger
_log = LazyLogger(__name__)

import sparkplug.timereporters.base

try:
    # pip install datadog
    from datadog import initialize

    import datadog.threadstats.base

    is_initialized = False

    class DDStatsd( sparkplug.timereporters.base.Base ):
        def __init__( self, aggregation_count, api_key, app_key ):
            super().__init__(aggregation_count)
            global is_initialized
            if not is_initialized:
                initialize( api_key=api_key, app_key=app_key )
                is_initialized = True
            self.exec = []
            self.erro = []
            self.wait = []
            self.statsd = datadog.threadstats.base.ThreadStats()
            self.statsd.start()

        def append_exec( self, delta ):
            self.exec.append( delta )
            if len( self.exec ) >= self.aggregation_count :
                mn, md, mx = sparkplug.timereporters.base.mn_md_mx( self.exec )
                del self.exec[:]
                self.statsd.timing('sparkplug.msg.exec', md)

        def append_erro( self, delta ):
            self.erro.append( delta )
            if len( self.erro ) >= self.aggregation_count :
                mn, md, mx = sparkplug.timereporters.base.mn_md_mx( self.erro )
                del self.erro[:]
                self.statsd.timing('sparkplug.msg.erro', md)

        def append_wait( self, delta ):
            self.wait.append( delta )
            if len( self.wait ) >= self.aggregation_count :
                mn, md, mx = sparkplug.timereporters.base.mn_md_mx( self.wait )
                del self.wait[:]
                self.statsd.timing('sparkplug.msg.wait', md)

        def __del__(self):
            self.statsd.stop()

except:

    class DDStatsd( sparkplug.timereporters.base.Base ):
        def __init__( self, aggregation_count, api_key, app_key ):
            super().__init__(aggregation_count)
            _log.warning( 'DDStatsd time_reporter unavailable, using noop' )
