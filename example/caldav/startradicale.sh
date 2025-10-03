#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


base_dir=$SCRIPT_DIR/../../tmp/radicale/collections
config_file=$SCRIPT_DIR/radicale-config


echo "Server dir: $base_dir"
echo "Server config: $config_file"

echo "Starting server. Available at: http://localhost:5232/"
echo "User: bob password: bob"

python3 -m radicale --storage-filesystem-folder=$base_dir --config=$config_file
