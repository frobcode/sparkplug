"""
Sends timing information to Datadog custom metrics

    [time_reporter:statsdtimer]
    # which class to instance?
    use = sparkplug#statsd
    # Tags to help with reporting:
    tags = service:myconsumer
    # Any extra parameters will be passed to statsdecor
    port = 8125
    host = localhost
    vendor = datadog
    # set to lower (eg. 0.1 or 0.01) if the load is too much
    default_sample_rate = 1

    [consumer:myconsumer]
    <blah>
    # I could use multiple timers like this: time_reporters = statsdtimer, myothertimer
    time_reporters = statsdtimer

Parameters:
    tags : list or None, optional, the list of key:value tags to associate
      with the sample sent to datadog
    extra parameters will be sent to the underlying statsdecor module, e.g.:
        port
        host
        vendor

"""

from sparkplug.logutils import LazyLogger
from sparkplug.timereporters.base import Base


_log = LazyLogger(__name__)


try:
    # pip install statsdecor
    import statsdecor
except ImportError:
    statsdecor = None


_log = LazyLogger(__name__)


class _Statsd(Base):

    def __init__(self, tags=None, **kwargs):
        super(_Statsd, self).__init__()

        # we can't rely on statsdecor to pass on the default sample rate. So we're doing it ourselves.
        if 'default_sample_rate' in kwargs:
            self.sample_rate = float(kwargs.pop('default_sample_rate'))
        else:
            # None doesn't float.
            self.sample_rate = None

        conf = {"prefix": "sparkplug"}
        conf.update(kwargs)
        # Don't share the global client, we might be
        # configured differently than the global:
        self.statsd = statsdecor._create_client(**conf)

        self.tags = self._parse_tags(tags)

    def _parse_tags(self, tags):
        ret = []
        if tags:
            ret = [x.strip() for x in tags.split(',')]
        return ret

    def append_exec(self, delta, tags=None):
        # This could be more interesting as a distribution.
        tags = self.tags + (tags or [])
        ms = delta.total_seconds()*1000
        self.statsd.timing('msg.exec', ms, tags=tags, rate=self.sample_rate)

    def append_erro(self, delta, tags=None):
        tags = self.tags + (tags or [])
        # deliberately leaving the sample rate off--if these are rare we want to see them.
        ms = delta.total_seconds()*1000
        self.statsd.timing('msg.erro', ms, tags=tags)

    def append_wait(self, delta, tags=None):
        # use "timing" instead of "distribution" because the data is pretty
        # monotonic: if there's a sudden backlog of messages in a FIFO queue,
        # then the timings should be roughly the same, going up a bit at a time..
        # the meaning will be in the values, not the distribution of those values.
        tags = self.tags + (tags or [])
        ms = delta.total_seconds()*1000
        self.statsd.timing('msg.wait', ms, tags=tags, rate=self.sample_rate)


class _NoopStatsd(Base):
    def __init__(self, tags=None, **kwargs):
        super(_NoopStatsd, self).__init__()


def Statsd(*args, **kwargs):
    if statsdecor is None:
        _log.warning('Statsd time_reporter unavailable, using noop. (Do you need to "pip install statsdecor"?)')
        return _NoopStatsd(*args, **kwargs)
    else:
        return _Statsd(*args, **kwargs)
