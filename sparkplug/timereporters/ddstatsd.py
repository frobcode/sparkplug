"""
Sends timing information to Datadog custom metrics
Uses a thread to send at regular intervals, without
interfering with the main consumer thread
"""

from sparkplug.logutils import LazyLogger
_log = LazyLogger(__name__)

from sparkplug.timereporters.base import Base, min_median_max

try:
    # pip install datadog
    from datadog import initialize

    from datadog.threadstats.base import ThreadStats

    is_initialized = False

    class DDStatsd(Base):
        def __init__(self, aggregation_count, api_key, app_key, tags=None):
            super(DDStatsd, self).__init__(aggregation_count)
            global is_initialized
            if not is_initialized:
                # Datadog docs are unclear whether initializing twice would be an issue.
                # Examples initialize in the scope of the module, which we can't
                # do because we don't have our keys yet.
                # Taking a safe position of not making the assumption that it's okay.
                initialize(api_key=api_key, app_key=app_key)
                is_initialized = True
            self.exec = []
            self.erro = []
            self.wait = []
            self.tags = self._parse_tags(tags)
            self.statsd = ThreadStats()
            self.statsd.start()

        def _parse_tags(self,tags):
            ret = None
            if tags :
                ret = [x.strip() for x in tags.split(',')]
            return ret

        def append_exec(self, delta):
            self.exec.append(delta)
            if len(self.exec) >= self.aggregation_count :
                mn, md, mx = min_median_max(self.exec)
                del self.exec[:]
                self.statsd.timing('sparkplug.msg.exec', md, tags=self.tags)

        def append_erro(self, delta):
            self.erro.append(delta)
            if len(self.erro) >= self.aggregation_count :
                mn, md, mx = min_median_max(self.erro)
                del self.erro[:]
                self.statsd.timing('sparkplug.msg.erro', md, tags=self.tags)

        def append_wait(self, delta):
            self.wait.append(delta)
            if len(self.wait) >= self.aggregation_count :
                mn, md, mx = min_median_max(self.wait)
                del self.wait[:]
                self.statsd.timing('sparkplug.msg.wait', md, tags=self.tags)

        def __del__(self):
            self.statsd.stop()

except ImportError:

    class DDStatsd(Base):
        def __init__(self, aggregation_count, api_key, app_key, tags=None):
            super().__init__(aggregation_count)
            _log.warning('DDStatsd time_reporter unavailable, using noop. (Do you need to "pip install datadog"?)')
