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
from datetime import datetime
import logging
import argparse
import copy
import pprint
from deepdiff import DeepDiff

from PyQt5.QtWidgets import QDialog

from hanlendar import logger

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.widget.taskdialog import TaskDialog

from hanlendar.domainmodel.recurrent import Recurrent
from hanlendar.domainmodel.local.task import LocalTask, Task
from hanlendar.domainmodel.calendardata import CalendarData


## ============================= main section ===================================


if __name__ != "__main__":
    sys.exit(0)


parser = argparse.ArgumentParser(description="Hanlendar Example")

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

parentTask = LocalTask()
parentTask.recurrence = Recurrent()
parentTask.recurrence.setWeekly(1)

item: Task = LocalTask()
item.setParent(parentTask)
item.commonData.calendar_id = "id_cal1"
item.title = "Task 1"
item.description = "description example"
item.completed = 50
item.priority = 5
# item.setDefaultDateTime(datetime.today().replace(hour=12, minute=0, second=0))
start = datetime.today().date()
end = datetime.today().replace(hour=14, minute=0, second=0)
item.setOccurrence(start, end)

while True:
    item_backup = copy.deepcopy(item)

    dialog = TaskDialog(item, calendar_data)
    ## dialog.resize(600, 800)
    ## root_path = get_root_path()
    ## renderToPixmap(dialog, root_path + "/tmp/taskdialog-big.png")
    exit_code = dialog.exec_()  ## returns QDialog::DialogCode: 0 - rejected, 1 - accepted

    item = dialog.task
    diff = DeepDiff(item_backup, item)
    changed = item != item_backup
    if changed:
        diff_str = pprint.pformat(diff)
        print(f"item changed, difference:\n{diff_str}")
    else:
        print("nothing changed")

    if changed != bool(diff):
        print("invalid equality operator")

    if exit_code == QDialog.Rejected:
        ## closed in other way than by closing window
        print("rejected:", exit_code)
        sys.exit(exit_code)
    elif exit_code == QDialog.Accepted:
        print("accepted:", exit_code)
    else:
        print("unknown exit code:", exit_code)
        sys.exit(exit_code)

    if not changed:
        sys.exit(exit_code)
