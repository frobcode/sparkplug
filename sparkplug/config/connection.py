"""Connection configuration
===========================

.. highlight:: ini

Every sparkplug instance is attached to a single ``connection``, usually
named ``main``. The connection contains all the information necessary to
connect to a single AMQP broker.

The simplest possible connection is::

    [connection:main]

which is equivalent to::

    [connection:main]
    # The host (or host:port) of the broker node to connect to.
    host = localhost
    # The virtual host to connect to.
    virtual_host = /
    # The user to connect as.
    userid = guest
    # The user's password.
    password = guest
    # If set, forces the use of SSL to connect to the broker.
    ssl = False
    # If set, changes the interval between reconnect attempts:
    reconnect_delay = 10
    # If set, overrides the default heartbeat interval (requested)
    heartbeat = 10
    # If set, overrides the quality-of-service message count to buffer.
    qos = 24

Sparkplug operates by starting a connection, then applying all other
configuration directives to it (to set up queues_, exchanges_, bindings_,
and consumers_), then waiting for messages to be delivered.

.. _queues: `Queue configuration`_
.. _exchanges: `Exchange configuration`_
.. _bindings: `Binding configuration`_
.. _consumers: `Consumer configuration`_
"""

import amqp
import time
import socket
import threading

from sparkplug.config.types import convert, parse_bool
from sparkplug.logutils import LazyLogger
from amqp import spec

_log = LazyLogger(__name__)


def _locked_call(lock, fn):
    # In an ideal world, we'd functool.wraps here,
    # but this complicates python 2.7 support and
    # isn't offering a lot of benefit in this context.
    def locked_fn(*args, **kwargs):
        with lock:
            r = fn(*args, **kwargs)
        return r
    return locked_fn


class MultiThreadedConnection(object):
    """
    Context Manager

    Replaces methods on connection, channel
    with ones that use a shared lock; to
    prevent the consumer and the heartbeater
    from stepping on each other between threads.
    """

    def __init__(self, connection, channel):
        self._connection = connection
        self._channel = channel
        self._connection_hold = {}
        self._channel_hold = {}
        self._lock = threading.RLock()

    def _lock_obj(self, obj, store):
        elements = set(dir(obj)) & set(['send_heartbeat', 'send_method'])
        for e in elements:
            attr = getattr(obj, e)
            if callable(attr):
                store[e] = attr
                setattr(obj, e, _locked_call(self._lock, attr))
        return

    def _unlock_obj(self, obj, store):
        for e in store:
            setattr(obj, e, store[e])
        store.clear()

    def __enter__(self):
        self._lock_obj(self._connection, self._connection_hold)
        self._lock_obj(self._channel, self._channel_hold)
        _log.debug("Connection frame_writer is serialized")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._unlock_obj(self._channel, self._channel_hold)
        self._unlock_obj(self._connection, self._connection_hold)
        _log.debug("Connection frame_writer is restored")
        return False


def jitter():
    "returns a quasi-random floating point value between 0 and 1"
    return (time.clock() * (879190747.0 ** 0.5)) % 1  # kronecker sequence


class AMQPConnector(object):
    def __init__(self, name, channel_configurer, reconnect_delay='10', qos=24, **kwargs):
        self.qos = int(qos)
        self.reconnect_delay = int(reconnect_delay)
        self.connection_args = dict(kwargs)
        convert(self.connection_args, 'ssl', parse_bool)
        convert(self.connection_args, 'heartbeat', int)

        if 'heartbeat' not in self.connection_args:
            self.connection_args['heartbeat'] = 15

        self.channel_configurer = channel_configurer

    def run_channel(self, connection, channel):
        _log.debug("Configuring channel elements.")
        self.channel_configurer.start(channel)
        try:
            self.pump(connection, channel)
        except (SystemExit, KeyboardInterrupt):
            _log.debug("Tearing down connection.")
            self.channel_configurer.stop(channel)
            raise

    def pump(self, connection, channel):
        timeout = connection.heartbeat * 0.4 or None
        while True:
            _log.debug("Waiting for a message.")
            try:
                channel.wait(spec.Basic.Deliver, timeout=timeout)
            except socket.timeout:
                _log.debug("Idle heartbeat")
                connection.send_heartbeat()

    def run(self):
        while True:
            try:
                _log.debug("Connecting to broker.")
                connection = amqp.Connection(**self.connection_args)
                connection.connect()  # populate properties
                channel = connection.channel()
                mtconnection = MultiThreadedConnection(connection, channel)
                with connection, mtconnection:
                    # you risk dropped tcp connections due to buffer overflow without setting qos:
                    _log.debug("Applying qos: {}".format(self.qos))
                    channel.basic_qos(0, self.qos, False)
                    with channel:
                        self.run_channel(connection, channel)

            except (SystemExit, KeyboardInterrupt):
                return
            except (IOError, socket.error):
                _log.exception(
                    "Connection error. Waiting %s seconds and trying again.",
                    self.reconnect_delay
                )
                # jitter:
                time.sleep(self.reconnect_delay + jitter())
            except:
                _log.exception(
                    "Unexpected exception. Waiting %s seconds and trying again.",
                    self.reconnect_delay
                )
                time.sleep(self.reconnect_delay + jitter())
