from __future__ import with_statement

try:
    from configparser import ConfigParser
except ImportError:
    # patch support for python 2.7
    import configparter.SafeConfigParser as ConfigParser
    ConfigParser.read_file = ConfigParser.readfp

import optparse
import logging
import logging.config
import os
import sys
import sparkplug.options
import sparkplug.config
import sparkplug.logutils
import sparkplug.executor

_log = sparkplug.logutils.LazyLogger(__name__)


def sparkplug_options(args):
    options = optparse.OptionParser(
        usage="%prog [options] CONFIG [CONFIG2 CONFIG3 ...]",
        description="An AMQP message handler.",
        option_class=sparkplug.options.Option
    )
    options.add_option("-c", "--connection",
                       action="store",
                       help="the name of the connection configuration to host (default: %default)",
                       default="main")
    options.add_option("-C", "--connector",
                       action="store",
                       help="overrides the connector implementation entry point (default: %default)",
                       default="connection")
    options.add_option("-j", "--fork",
                       action="store",
                       type="int",
                       help="runs multiple parallel consumers with identical configurations",
                       default=None)
    return options.parse_args(args)


def collate_configs(filenames, defaults):
    _log.debug("Loading configuration files: %r", filenames)

    config = ConfigParser(defaults)

    for filename in filenames:
        with open(filename, 'r') as config_file:
            config.read_file(config_file)

    return config


def start_logging(filenames, configure=logging.config.fileConfig):
    for filename in filenames:
        # Ensure 'filename' exists and is readable. fileConfig will open it a
        # second time anyways.
        with open(filename, 'r') as file:
            configure(filename)


def run_sparkplug(
    options,
    conf_files,
    configparse=collate_configs,
    configurer_factory=sparkplug.config.create_configurer,
    connector_factory=sparkplug.config.create_connector,
    configure_logging=start_logging,
    worker_number=0
):
    configure_logging(conf_files)

    defaults = {'worker-number': str(worker_number)}
    config = configparse(conf_files, defaults)
    channel_configurer = configurer_factory(
        config,
        defaults,
        options.connector
    )
    connector = connector_factory(
        config,
        channel_configurer,
        options.connector,
        options.connection
    )

    try:
        _log.info("Starting sparkplug.")
        connector.run()
    except (SystemExit, KeyboardInterrupt):
        print  # GNU Readline hates dangling ^Cs.
    _log.info("Exiting sparkplug normally.")


def main(
    args=sys.argv[1:],
    optparse=sparkplug_options,
    daemon_entry_point=run_sparkplug
):
    options, conf_files = optparse(args)
    executor = sparkplug.executor.direct
    if options.fork:
        executor = sparkplug.executor.Subprocess(options.fork)

    try:
        executor(daemon_entry_point, options, conf_files)
    except (SystemExit, KeyboardInterrupt):
        _log.debug("Exiting sparkplug CLI.")
