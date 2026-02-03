#!/bin/bash

set -eu


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


SRC_DIR="$SCRIPT_DIR/../src"


## $1 - output base name
## $2 - script path
generate_tools_help() {
    local out_base_name="${1}"
    local script_path="${2}"

    HELP_MD_PATH="$SCRIPT_DIR/${out_base_name}.md"
    HELP_TXT_PATH="$SCRIPT_DIR/${out_base_name}.txt"

    cd "$SRC_DIR"

    COMMAND="${script_path}"
    COMMAND_TEXT=$(basename "${COMMAND}")

    echo "## <a name=\"main_help\"></a> $COMMAND_TEXT --help" > "${HELP_MD_PATH}"
    echo -e "\`\`\`" >> "${HELP_MD_PATH}"
    $COMMAND --help >> "${HELP_MD_PATH}"
    echo -e "\`\`\`" >> "${HELP_MD_PATH}"

    echo -e "\`\`\`" > "${HELP_TXT_PATH}"
    $COMMAND --help >> "${HELP_TXT_PATH}"
    echo -e "\`\`\`" >> "${HELP_TXT_PATH}"


    FAILED=0
    tools=$($COMMAND --listtools 2> /dev/null) || FAILED=1

    if [ $FAILED -eq 0 ]; then
        IFS=', ' read -r -a tools_list <<< "$tools"

        for item in "${tools_list[@]}"; do
            echo "checking tool: $item"

            echo -e "\n\n" >> "${HELP_MD_PATH}"
            echo "## <a name=\"${item}_help\"></a> $COMMAND_TEXT $item --help" >> "${HELP_MD_PATH}"
            echo -e "\`\`\`" >> "${HELP_MD_PATH}"
            $COMMAND "$item" --help >> "${HELP_MD_PATH}"
            echo -e "\`\`\`"  >> "${HELP_MD_PATH}"

            echo -e "\n\n" >> "${HELP_TXT_PATH}"
            echo -e "\`\`\`" >> "${HELP_TXT_PATH}"
            $COMMAND "$item" --help >> "${HELP_TXT_PATH}"
            echo -e "\`\`\`" >> "${HELP_TXT_PATH}"
        done
    else
        echo "no --listtools found"
    fi
}


generate_tools_help "hanlendar-cmdargs" "$SRC_DIR/startcalendar"
generate_tools_help "managecals-cmdargs" "$SRC_DIR//managecals.py"
generate_tools_help "caldavmanager-cmdargs" "$SRC_DIR/../example/caldav/caldavmanager.py"


"$SCRIPT_DIR"/generate_small.sh
