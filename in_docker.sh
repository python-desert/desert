#!/bin/bash

eval "$(pyenv init -)"

pyenv shell "${TOXTOOLPYTHON}" $(pyenv global)

pip install tox
virtualenv --version
easy_install --version
pip --version
tox --version
tox -v
