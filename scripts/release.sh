#!/usr/bin/env bash
set -e

# Dependencies
pip install twine
make clean
make build
ls -l dist

# Push
export TWINE_USERNAME=${PYPI_USER}
export TWINE_PASSWORD=${PYPI_PASS}
twine upload --verbose  --repository-url ${PYPI_HOST} dist/*
