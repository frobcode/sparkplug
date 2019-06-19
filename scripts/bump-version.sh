#!/usr/bin/env bash
set -e

# Needs to be run from the root directory of the project
pip install bumpversion

# Increment version
bumpversion ${VERSION_BUMP_TYPE} setup.py
