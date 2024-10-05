#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


echo "generating docs"
"$SCRIPT_DIR"/doc/generate-doc.sh

echo "checking markdown files"
"$SCRIPT_DIR"/tools/mdpreproc.py "$SCRIPT_DIR/README.md"

echo "running tests under venv"
# run tests in venv (it verifies required packages)
"$SCRIPT_DIR"/tools/installvenv.sh --no-prompt
"$SCRIPT_DIR"/venv/runtests.py

if [ -f "$SCRIPT_DIR/examples/generate-all.sh" ]; then
	echo "generating examples results"
    "$SCRIPT_DIR"/examples/generate-all.sh
fi

echo "checking code"
"$SCRIPT_DIR"/tools/checkall.sh


echo "processing completed"
