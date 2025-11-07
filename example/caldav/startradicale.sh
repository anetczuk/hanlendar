#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


BASE_DIR="${SCRIPT_DIR}"/../../tmp/radicale
CONFIG_FILE="${SCRIPT_DIR}"/radicale-config
AUTH_PATH="${SCRIPT_DIR}"/auth.json


caldav_user=$(cat "${AUTH_PATH}" | jq -r ".user")
caldav_pass=$(cat "${AUTH_PATH}" | jq -r ".password")


RADICALE_AUTH="/tmp/radicale_user"

echo "${caldav_user}:${caldav_pass}" > "${RADICALE_AUTH}"


echo "Server dir: ${BASE_DIR}"
echo "Server config: ${CONFIG_FILE}"

echo "User: ${caldav_user}"
echo "Pass: ${caldav_pass}"

echo
echo "Starting server. Available at: http://localhost:5232/"
echo

python3 -m radicale --config="${CONFIG_FILE}" --storage-filesystem-folder="${BASE_DIR}"
