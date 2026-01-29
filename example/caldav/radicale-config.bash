##
## Configuration for radicale server.
##


## works both under bash and sh (works on direct call and when sourcing)
CONFIG_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")


export RADICALE_CONFIG_FILE="${CONFIG_DIR}"/radicale-config
export RADICALE_STORAGE_DIR="${CONFIG_DIR}"/../../tmp/radicale


### prepare config data
RADICALE_CONFIG_DIR="/tmp/radicale"

mkdir -p "${RADICALE_CONFIG_DIR}"


## prepare auth file
RADICALE_AUTH="${RADICALE_CONFIG_DIR}/auth_user"

AUTH_PATH="${CONFIG_DIR}"/auth.json

caldav_users=$(cat "${AUTH_PATH}" | jq -r '.users[].user')
caldav_passes=$(cat "${AUTH_PATH}" | jq -r '.users[].password')

mapfile -t user_arr <<< "${caldav_users}"
mapfile -t pass_arr <<< "${caldav_passes}"

truncate -s 0 "${RADICALE_AUTH}"
for i in "${!user_arr[@]}"; do
    echo "${user_arr[i]}:${pass_arr[i]}" >> "${RADICALE_AUTH}"
done

echo "Created accounts:"
cat "${RADICALE_AUTH}"


## prepare rights file
RADICALE_RIGHTS="${RADICALE_CONFIG_DIR}/rights"
cp "${SCRIPT_DIR}/rights" "${RADICALE_RIGHTS}"


echo
echo "Starting server. Available at: http://localhost:5232/"
echo
