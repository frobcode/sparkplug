
from datetime import timedelta

try:
    from unittest import mock
except ImportError:
    # because python2
    import mock


def ms(millis):
    return timedelta(milliseconds=millis)


@mock.patch('sparkplug.timereporters.statsd.statsdecor')
def test_shakedown(statsdecor):
    statsd = statsdecor._create_client()

    from sparkplug.timereporters.statsd import Statsd

    s = Statsd(tags='version:1')
    s.append_exec(ms(123), tags=['hello:yes'])
    statsd.timing.assert_called_once_with('msg.exec', 123, tags=['version:1', 'hello:yes'], rate=None)
    statsd.timing.reset_mock()

    s.append_wait(ms(124), tags=['hello:yes2'])
    statsd.timing.assert_called_once_with('msg.wait', 124, tags=['version:1', 'hello:yes2'], rate=None)
    statsd.timing.reset_mock()

    s.append_erro(ms(125), tags=['hello:yes3'])
    statsd.timing.assert_called_once_with('msg.erro', 125, tags=['version:1', 'hello:yes3'])
    statsd.timing.reset_mock()

    s = Statsd(tags='version:2', default_sample_rate=0.1)
    s.append_wait(ms(126), tags=['hello:yes4'])
    statsd.timing.assert_called_once_with('msg.wait', 126, tags=['version:2', 'hello:yes4'], rate=0.1)
    statsd.timing.reset_mock()

    s = Statsd(tags='version:2', default_sample_rate=0.1)
    s.append_erro(ms(126), tags=['hello:yes4'])
    statsd.timing.assert_called_once_with('msg.erro', 126, tags=['version:2', 'hello:yes4'])
    statsd.timing.reset_mock()


@mock.patch('sparkplug.timereporters.statsd.statsdecor')
def test_null(statsdecor):
    statsd = statsdecor._create_client()

    from sparkplug.timereporters.statsd import Statsd

    s = Statsd()
    s.append_exec(ms(123))
    statsd.timing.assert_called_once_with('msg.exec', 123, tags=[], rate=None)
    statsd.timing.reset_mock()

    s.append_wait(ms(124))
    statsd.timing.assert_called_once_with('msg.wait', 124, tags=[], rate=None)
    statsd.timing.reset_mock()

    s.append_erro(ms(125))
    statsd.timing.assert_called_once_with('msg.erro', 125, tags=[])
    statsd.timing.reset_mock()


@mock.patch('sparkplug.timereporters.statsd.statsdecor', new=None)
def test_no_statsdecor():
    from sparkplug.timereporters.statsd import Statsd
    from sparkplug.timereporters.statsd import statsdecor
    assert statsdecor is None

    s = Statsd()
    s.append_exec(ms(123), tags=['doesnt:matter'])
    s.append_wait(ms(124), tags=['doesnt:matter'])
    s.append_erro(ms(125), tags=['doesnt:matter'])
