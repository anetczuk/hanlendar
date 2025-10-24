#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


CACHE_DIR=$SCRIPT_DIR/../tmp/.mypy_cache


src_dir=$SCRIPT_DIR/../src

examples_dir=$SCRIPT_DIR/../example
if [ ! -d "$examples_dir" ]; then
    examples_dir=""
fi

all_examples=""
if [ -d "$examples_dir" ]; then
    all_examples=$(find "$examples_dir" -type f -name "*.py")
fi

src_examples=$(find "$src_dir" -type f -name "*.py" -not -path "$src_dir/build/*")


echo
echo "running mypy"
echo "ignore line warning using: # type: ignore[code]"

MYPY_ERR_PATH="/tmp/mypy.err.txt"
FAILED=0
# shellcheck disable=SC2086
mypy --cache-dir "$CACHE_DIR" --no-strict-optional --ignore-missing-imports --pretty --check-untyped-defs \
     $src_examples $all_examples 2> "$MYPY_ERR_PATH" || FAILED=1

if [ $FAILED -ne 0 ]; then
    cat "$MYPY_ERR_PATH"
    # shellcheck disable=SC2002
    ASSERTION=$(cat $MYPY_ERR_PATH | grep "AssertionError:")
    if [ "$ASSERTION" == "" ]; then
        exit 1
    else
        # mypy internal error
        echo "detected mypy internal error"
    fi
else
    echo "mypy finished"
fi
