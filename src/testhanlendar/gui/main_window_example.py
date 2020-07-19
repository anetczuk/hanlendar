#!/usr/bin/python3
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


try:
    ## following import success only when file is directly executed from command line
    ## otherwise will throw exception when executing as parameter for "python -m"
    # pylint: disable=W0611
    import __init__
except ImportError as error:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys
import logging
import argparse

from datetime import datetime, timedelta

import hanlendar.logger as logger

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.main_window import MainWindow

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.recurrent import Recurrent


# pylint: disable=R0914, R0915
def prepare_example_data( dataManager: Manager ):
    taskDate = datetime.today() - timedelta( seconds=5 )
    task1 = dataManager.addNewTaskDateTime( datetime.today() + timedelta( days=1 ), "task 1" )
    task1.completed = 50
    task1.description = ("<a href=\"http://www.google.com\">xxx</a> <br> "
                         "<a href=\"file:///media/E/bluetooth.txt\">yyy</a> <br> "
                         "<a href=\"file:///media/E/Pani1.jpg\">zzz</a>")

    completedTask = dataManager.addNewTaskDateTime( taskDate + timedelta( days=7 ), "completed task" )
    completedTask.setCompleted()

    ## add far task
    dataManager.addNewTaskDateTime( datetime.today() + timedelta( days=360 ), "far task" )

    recurrentTask = dataManager.addNewTaskDateTime( taskDate.replace( day=20, hour=12 ), "recurrent task 1" )
    recurrentTask.recurrence = Recurrent()
    recurrentTask.recurrence.setDaily()
    recurrentTask.recurrence.endDate = recurrentTask.getReferenceInitDateTime().date() + timedelta( days=2 )
    reminder = recurrentTask.addReminder()
    reminder.setDays( 1 )

    task2 = dataManager.addNewTaskDateTime( recurrentTask.startDateTime.replace( hour=11 ), "task 2" )
    task2.dueDateTime = task2.dueDateTime.replace( hour=20 )

    completedTask = dataManager.addNewTaskDateTime( task2.startDateTime - timedelta(hours=3), "completed task 2" )
    completedTask.setCompleted()

    recurrentDate2 = datetime.today().replace( day=15 ) + timedelta( days=30 )
    recurrentTask2 = dataManager.addNewTaskDateTime( recurrentDate2, "recurrent task 2" )
    recurrentTask2.setDeadline()
    recurrentTask2.recurrence = Recurrent()
    recurrentTask2.recurrence.setMonthly()

    deadlineDate = datetime.today() + timedelta( seconds=10 )
    deadlineTaks = dataManager.addNewDeadlineDateTime( deadlineDate, "expired task 1" )
    reminder = deadlineTaks.addReminder()
    reminder.setMillis( 5000 )

    remindedTask = dataManager.addNewTaskDateTime( datetime.today() + timedelta( hours=2 ), "reminded task 1" )
    reminder = remindedTask.addReminder()
    reminder.setDays( 30 )

    todo1 = dataManager.addNewToDo("ToDo example A")
    todo1.description = "a description"
    todo1.priority = 3
    todo1.completed = 33
    todo1 = dataManager.addNewToDo("ToDo example B")
    todo1.description = "a description"
    todo1.priority = 3
    todo1.completed = 33
    todo1 = dataManager.addNewToDo("ToDo example C")
    todo1.description = "a description"
    todo1.priority = 3
    todo1.completed = 33

    todo2 = dataManager.addNewToDo("ToDo example 2")
    todo2.description = "a description"
    todo2.priority = 5
    todo2.completed = 20

    todo2 = dataManager.addNewToDo("ToDo example 3")
    todo2.description = "a description"
    todo2.priority = 1
    todo2.completed = 0

    todoCompleted = dataManager.addNewToDo("completed ToDo 1")
    todoCompleted.description = "a description"
    todoCompleted.priority = 1
    todoCompleted.completed = 100

    dataManager.addNote("note 2", "note content")


def save_data_mock():
    _LOGGER.info("saving data is disabled on example")


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


parser = argparse.ArgumentParser(description='Hanlendar Example')
parser.add_argument('-lud', '--loadUserData', action='store_const', const=True, default=False, help='Load user data' )

args = parser.parse_args()


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")

MainWindow.toolTip = MainWindow.toolTip + " Preview"

window = MainWindow()
# pylint: disable=W0212
window._saveData = save_data_mock           # type: ignore
window.setWindowTitle( window.windowTitle() + " Preview" )

window.loadSettings()
if args.loadUserData:
    window.loadData()
else:
    manager = window.getManager()
    prepare_example_data( manager )
    window.refreshView()

window.show()

setup_interrupt_handling()

exitCode = app.exec_()

if exitCode == 0:
    window.saveSettings()

sys.exit( exitCode )
