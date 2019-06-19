#!/usr/bin/env bash
set -e

# Dependencies
pip install devpi-client
make clean
make build
ls -l dist

# Push
devpi use ${PYPI_INDEX}
devpi login ${PYPI_USER} --password=${PYPI_PASS}
devpi upload dist/sparkplug-*
