#!/bin/bash

set -eu

## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


big_suffix="-big."
small_suffix="-small."

for filename in $SCRIPT_DIR/*.png; do
    if [[ $filename != *"$big_suffix"* ]]; then
        continue
    fi
    small_name=${filename/$big_suffix/$small_suffix}
    echo "converting: $filename -> $small_name"
    convert $filename -resize 400 $small_name
    #convert $filename -resize 200x100 $small_name
done
