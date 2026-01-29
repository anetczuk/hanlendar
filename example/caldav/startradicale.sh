#!/bin/bash

##
## Helper script for running radicale server.
##
## Required:
##      pip3 install radicale --break-system-packages
##

set -eu


## works both under bash and sh (works on direct call and when sourcing)
SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")


print_usage() {
    SCRIPT_NAME=$(basename "$(readlink -f "${BASH_SOURCE[0]}")")
    
    cat << EOF
Script for starting radicale server.

usage: ${SCRIPT_NAME} [OPTIONS]

options:
    -h, --help          -- this information
    --bashcfg [PATH]    -- path to bash file with additional configuration
    --lldebug           -- same as "--logging-level debug"
EOF

    echo
    echo
    echo "radicale options:"
    echo

    python3 -m radicale --help
}


## args to preserve
args=()

BASH_CFG=""

while [[ $# -gt 0 ]]; do
    case $1 in
      -h|--help)    print_usage
                    exit 0
                    ;;

      --bashcfg)    BASH_CFG="${2}"
                    shift 2             ## past argument
                    ;;

      --bashcfg=*)  BASH_CFG="${1#*=}"
                    shift               ## past argument
                    ;;

      --lldebug)    args+=("--logging-level" "debug")
                    shift               ## past argument
                    ;;

      *)    args+=("${1}")      ## preserve arg
            shift               ## past argument
            ;;
    esac
done

## restore args
set -- "${args[@]}"


if [[ "${BASH_CFG}" == "" ]]; then
    ## sourcing default file

    DEFAULT_BASH_CFG="${SCRIPT_DIR}/radicale-config.bash"
    if [[ -f "${DEFAULT_BASH_CFG}" ]]; then
        echo "Importing config: ${DEFAULT_BASH_CFG}"
        echo
    
        # shellcheck disable=SC1091,SC1090
        source "${DEFAULT_BASH_CFG}"
    fi
else
    echo "Importing config: ${BASH_CFG}"
    echo

    # shellcheck disable=SC1090
    source "${BASH_CFG}"
fi


echo "Server config: ${RADICALE_CONFIG_FILE}"
echo "Server storage: ${RADICALE_STORAGE_DIR}"
echo

python3 -m radicale --config="${RADICALE_CONFIG_FILE}" --storage-filesystem-folder="${RADICALE_STORAGE_DIR}" "${@}"
