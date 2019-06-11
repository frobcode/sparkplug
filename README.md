# Sparkplug

[![Build Status](https://www.travis-ci.org/freshbooks/sparkplug.svg?branch=master)](https://www.travis-ci.org/freshbooks/sparkplug)
[![PyPi version](https://img.shields.io/pypi/v/sparkplug.svg)](https://pypi.org/project/sparkplug/)

Sparkplug is a lightweight AMQP message consumer. It allows you to specify queue configuration and consumer entry points using INI files

## Testing
run tests with `nosetests`

## Releasing
To create a new release commit run:
```bash
./bump.sh
git push origin master
git push --tags
```
A new release will be automatically generated on the tag build.

Version 1.11.5, 1.11.6, 1.12.0 are Python 2.7 and 3.x compatible.
