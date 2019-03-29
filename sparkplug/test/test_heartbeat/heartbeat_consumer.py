import sys
import time
from sparkplug.logutils import LazyLogger

_log = LazyLogger(__name__)


class HeartbeatConsumer(object):
    def __init__(self, channel ):
        self.channel = channel
        self.counter = 0
        self.timeouts = ([0] * (8 * 1024)) + [0.125,0,1,2,3,4,0,8,16,24,16] + ([0] * (8 * 1024))

    def __call__(self, msg):
        timeout = self.timeouts[ self.counter ]
        self.counter = (self.counter + 1) % len( self.timeouts )
        if timeout :
            time.sleep( timeout )
        local_body = str( msg.body )
        _log.debug( "count down: {}".format( local_body ))
        self.channel.basic_ack(msg.delivery_tag)
