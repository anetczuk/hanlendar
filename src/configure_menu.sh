#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
AUTOSTART_FILE=~/.local/share/applications/menulibre-todocalendar.desktop


cat > $AUTOSTART_FILE << EOL
[Desktop Entry]
Version=1.1
Type=Application
Name=ToDo Calendar
Comment=A small descriptive blurb about this application.
Icon=$SCRIPT_DIR/calendar/gui/img/calendar-black.png
Exec=$SCRIPT_DIR/startcalendar
Path=$SCRIPT_DIR
Actions=
Categories=Office;
StartupNotify=true
Terminal=false

EOL


echo "File created in: $AUTOSTART_FILE"
