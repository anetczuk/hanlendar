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


import sys
import os


#### append local library
sys.path.append(os.path.abspath( os.path.join(os.path.dirname(__file__), "../..") ))


import logging

import hanlendar.logger as logger

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.main_window import MainWindow
from hanlendar.domainmodel.recurrent import Recurrent
from hanlendar.domainmodel.reminder import Reminder

from datetime import date, datetime, timedelta


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


def prepareExampleData( window: MainWindow ):
    dataManager = window.getManager()
    taskDate = datetime.today() - timedelta( seconds=5 )
    task1 = dataManager.addNewTaskDateTime( datetime.today() + timedelta( days=1 ), "task 1" )
    task1.completed = 50
    task1.description = "<a href=\"http://www.google.com\">xxx</a> <br> <a href=\"file:///media/E/bluetooth.txt\">yyy</a> <br> <a href=\"file:///media/E/Pani1.jpg\">zzz</a>"

    completedTask = dataManager.addNewTaskDateTime( taskDate + timedelta( days=7 ), "completed task" )
    completedTask.setCompleted()

    ## add far task
    dataManager.addNewTaskDateTime( datetime.today() + timedelta( days=360 ), "far task" )

    recurrentTask = dataManager.addNewTaskDateTime( taskDate.replace( day=20, hour=12 ), "recurrent task 1" )
    recurrentTask.recurrence = Recurrent()
    recurrentTask.recurrence.setDaily()
    recurrentTask.recurrence.endDate = recurrentTask.getReferenceDateTime().date() + timedelta( days=2 )
    reminder = recurrentTask.addReminder()
    reminder.setDays( 1 )

    task2 = dataManager.addNewTaskDateTime( recurrentTask.startDate.replace( hour=11 ), "task 2" )
    task2.dueDate = task2.dueDate.replace( hour=20 )

    completedTask = dataManager.addNewTaskDateTime( task2.startDate - timedelta(hours=3), "completed task 2" )
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

    window.refreshView()


logFile = logger.getLoggingOutputFile()
logger.configure( logFile )


_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

MainWindow.toolTip = MainWindow.toolTip + " Preview"

window = MainWindow()
# window.ui.actionSave_data.setEnabled( False )
window.loadSettings()


def save_data_mock():
    _LOGGER.info("saving data is disabled on example")


window._saveData = save_data_mock           # type: ignore

prepareExampleData( window )

window.show()

setup_interrupt_handling()

exitCode = app.exec_()

if exitCode == 0:
    window.saveSettings()

sys.exit( exitCode )