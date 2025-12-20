#!/usr/bin/env python3
#
# MIT License
#
# Copyright (c) 2017 Arkadiusz Netczuk <dev.arnet@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# ruff: noqa: T201 (`print` found)

import contextlib

with contextlib.suppress(ImportError):
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=E0401,W0611
    # ruff: noqa: F401
    import __init__

    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded

import sys
import logging
import datetime
import argparse
import copy
import pprint
from deepdiff import DeepDiff

from hanlendar import logger

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.widget.tododetails import ToDoDetails

from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.domainmodel.calendardata import CalendarData


## ============================= main section ===================================


if __name__ != "__main__":
    sys.exit(0)


parser = argparse.ArgumentParser(description="Hanlendar Example")
parser.add_argument("-ro", "--readonly", action="store_const", const=True, default=False, help="Read-only mode")

args = parser.parse_args()


logFile = logger.get_logging_output_file()
logger.configure(logFile)

_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

setup_interrupt_handling()

calendar_data = CalendarData()
calendar_data.addCalendar("cal1", "id_cal1", enabled=True)
calendar_data.addCalendar("cal2", "id_cal2", enabled=True)

todo = LocalToDo()
todo.commonData.calendar_id = "id_cal1"
todo.title = "Task title"
todo.description = "Description\nwww.google.pl"
todo.url = "http://www.google.pl"
todo.completed = 50
todo.priority = 5
start = datetime.datetime.today().date()
end = datetime.datetime.today().replace(hour=14, minute=0, second=0)
todo.setStartDateTime(start)
todo.setDueDateTime(end)
todo._common_data.unknown_props = {"aaa": "bbb"}  # pylint: disable=W0212

while True:
    todo_backup = copy.deepcopy(todo)

    widget = ToDoDetails()
    widget.setCalendarData(calendar_data)
    widget.setReadOnly(read_only=args.readonly)
    widget.setToDo(todo)
    widget.show()

    exit_code = app.exec_()
    if exit_code != 0:
        ## closed in other way than by closing window
        print("interrupt exit", exit_code)
        sys.exit(exit_code)

    diff = DeepDiff(todo_backup, todo)
    changed = todo != todo_backup
    if changed:
        diff_str = pprint.pformat(diff)
        print(f"item changed, difference:\n{diff_str}")
    else:
        print("nothing changed")

    if changed != bool(diff):
        print("invalid equality operator")

    if not changed:
        sys.exit(exit_code)
