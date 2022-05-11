#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
AUTOSTART_FILE=~/.local/share/applications/menulibre-hanlendar.desktop


cat > $AUTOSTART_FILE << EOL
[Desktop Entry]
Name=Hanlendar
GenericName=Hanlendar
Comment=Calendar and todo list in one application.
Version=1.1
Type=Application
Exec=$SCRIPT_DIR/startcalendar %U
Path=$SCRIPT_DIR
Icon=$SCRIPT_DIR/hanlendar/gui/img/calendar-bw.png
Actions=
Categories=Office;
StartupNotify=true
Terminal=false

EOL


echo "File created in: $AUTOSTART_FILE"
