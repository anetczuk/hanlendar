#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


RADICALE_CONF_DIR="/tmp/radicale"

BASE_DIR="${SCRIPT_DIR}"/../../tmp/radicale
CONFIG_FILE="${SCRIPT_DIR}"/radicale-config
AUTH_PATH="${SCRIPT_DIR}"/auth.json


mkdir -p "${RADICALE_CONF_DIR}"


RADICALE_AUTH="${RADICALE_CONF_DIR}/auth_user"

caldav_users=$(cat "${AUTH_PATH}" | jq -r '.users[].user')
caldav_passes=$(cat "${AUTH_PATH}" | jq -r '.users[].password')

mapfile -t user_arr <<< "${caldav_users}"
mapfile -t pass_arr <<< "${caldav_passes}"

truncate -s 0 "${RADICALE_AUTH}"
for i in "${!user_arr[@]}"; do
    echo "${user_arr[i]}:${pass_arr[i]}" >> "${RADICALE_AUTH}"
done


RADICALE_RIGHTS="${RADICALE_CONF_DIR}/rights"
cp "${SCRIPT_DIR}/rights" "${RADICALE_RIGHTS}"


echo "Server dir: ${BASE_DIR}"
echo "Server config: ${CONFIG_FILE}"

echo "Accounts:"
cat "${RADICALE_AUTH}"

echo
echo "Starting server. Available at: http://localhost:5232/"
echo

python3 -m radicale --config="${CONFIG_FILE}" --storage-filesystem-folder="${BASE_DIR}" "${@}"
