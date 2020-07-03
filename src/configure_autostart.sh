#!/bin/bash


## works both under bash and sh
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")


## add udev rule
AUTOSTART_FILE=~/.config/autostart/ToDoCalendar.desktop


cat > $AUTOSTART_FILE << EOL
[Desktop Entry]
Name=ToDo Calendar
GenericName=ToDo Calendar
Comment=Calendar and ToDo list in one application.
Type=Application
Categories=Office;
Exec=$SCRIPT_DIR/startcalendar --minimized
Icon=$SCRIPT_DIR/todocalendar/gui/img/calendar-bw.png
Terminal=false
StartupNotify=true
X-GNOME-Autostart-enabled=true
EOL


echo "File created in: $AUTOSTART_FILE"