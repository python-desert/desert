#!/bin/bash

eval "$(pyenv init -)"

pyenv shell 3.8.1
pip install tox
virtualenv --version
easy_install --version
pip --version
tox --version
tox -v
