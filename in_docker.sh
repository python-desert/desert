#!/bin/bash

set -vx

eval "$(pyenv init -)"

pip install tox
virtualenv --version
easy_install --version
pip --version
tox --version
tox -v
