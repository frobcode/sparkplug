import sys
import time
import json
import amqp
from sparkplug.logutils import LazyLogger

_log = LazyLogger(__name__)


class HeartbeatConsumer(object):
    def __init__(self, channel):
        self.channel = channel
        self.timeouts = ([0] * (8 * 1024)) + [0.125, 0, 1, 2, 3, 4, 0,8,16,24,16] + ([0] * (8 * 1024))

    def __call__(self, msg):
        counter = int(json.loads(msg.body))
        if 0 == (counter % 8192):
            self.channel.basic_ack(msg.delivery_tag)
            raise RuntimeError(
                "Intentional Exception on value {}.\nDoes the sparkplug recover gracefully?".format(counter))

        if 0 == (counter % 1024):
            routing_key = 'events'
            exchange = 'postoffice'
            _log.info("REQUEUE {}".format(counter))
            # this is an anti-pattern, but it does occur.  Make sure we can support it:
            self.channel.basic_publish(amqp.Message('1'+msg.body), exchange=exchange, routing_key=routing_key)
            self.channel.basic_ack(msg.delivery_tag)
            return

        timeout = self.timeouts[counter % len(self.timeouts)]
        if timeout:
            time.sleep(timeout)

        local_body = str(msg.body)
        _log.debug("count down: {} (sleep {})".format(local_body, timeout))
        self.channel.basic_ack(msg.delivery_tag)
