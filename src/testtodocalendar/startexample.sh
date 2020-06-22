#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


cd $SCRIPT_DIR


echo "starting the app"

exit_code=0
# python3 -m testtodocalendar.gui.main_window_example "$@" && exit_code=$? || exit_code=$?
python3 gui/main_window_example.py "$@" && exit_code=$? || exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo "abnormal application exit: $exit_code"
fi


echo "Done"
