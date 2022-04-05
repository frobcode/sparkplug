from sparkplug.logutils import LazyLogger
_log = LazyLogger(__name__)


class SignalHandler:
    should_terminate = False

    @classmethod
    def signal_handler(cls, sig, frame):
        _log.warning("Signal %s received, setting `should_terminate` flag", sig)
        SignalHandler.should_terminate = True
