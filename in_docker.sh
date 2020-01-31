#!/bin/bash

set -vx

pip install tox
virtualenv --version
easy_install --version
pip --version
tox --version
tox -v
