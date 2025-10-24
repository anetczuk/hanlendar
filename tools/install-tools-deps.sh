#!/bin/bash

set -eu


sudo apt install black pycodestyle flake8 pylint bandit shellcheck
pip3 install safety

sudo apt install pydocstyle

sudo apt install mypy

#pip3 install --user -I git+https://github.com/anetczuk/mdlinkscheck.git#subdirectory=src
pip3 install -I git+https://github.com/anetczuk/mdlinkscheck.git#subdirectory=src
