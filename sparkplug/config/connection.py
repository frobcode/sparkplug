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

Sparkplug operates by starting a connection, then applying all other
configuration directives to it (to set up queues_, exchanges_, bindings_,
and consumers_), then waiting for messages to be delivered.

.. _queues: `Queue configuration`_
.. _exchanges: `Exchange configuration`_
.. _bindings: `Binding configuration`_
.. _consumers: `Consumer configuration`_
"""

from __future__ import with_statement

import amqp
import time
import socket
from sparkplug.config.types import convert, parse_bool
from sparkplug.logutils import LazyLogger
from amqp import spec

_log = LazyLogger(__name__)


class AMQPConnector(object):
    def __init__(self, name, channel_configurer, reconnect_delay='10', **kwargs):
        self.reconnect_delay = int(reconnect_delay)
        self.connection_args = dict(kwargs)
        convert(self.connection_args, 'ssl', parse_bool)
        convert(self.connection_args, 'heartbeat', int)

        if 'heartbeat' not in self.connection_args:
            self.connection_args['heartbeat'] = 60

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
        while True:
            _log.debug("Waiting for a message.")
            try:
                channel.wait(spec.Basic.Deliver, timeout=connection.heartbeat)
            except socket.timeout :
                if connection.heartbeat:
                    connection.send_heartbeat() # overkill: should be able to use heartbeat_tick()

    def run(self):
        while True:
            try:
                _log.debug("Connecting to broker.")
                with amqp.Connection(**self.connection_args) as connection:
                    with connection.channel() as channel:
                        self.run_channel(connection, channel)

            except (SystemExit, KeyboardInterrupt):
                return
            except (IOError, socket.error):
                _log.exception(
                    "Connection error. Waiting %s seconds and trying again.",
                    self.reconnect_delay
                )
                time.sleep(self.reconnect_delay)
            except:
                _log.exception(
                    "Unexpected exception. Waiting %s seconds and trying again.",
                    self.reconnect_delay
                )
                time.sleep(self.reconnect_delay)
