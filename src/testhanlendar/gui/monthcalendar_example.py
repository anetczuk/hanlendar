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

from datetime import datetime, timedelta

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.monthcalendar import MonthCalendar
from hanlendar.gui.dataobject import DataObject

from hanlendar.domainmodel.recurrent import Recurrent


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

setup_interrupt_handling()

dataObject = DataObject( None )

todayDate = datetime.today().replace( hour=6 )
task1 = dataObject.addTask()
task1.title = "Task 1"
task1.startDate = todayDate + timedelta( hours=5 )
task1.dueDate   = task1.startDate + timedelta( hours=5 )

refDate = todayDate + timedelta( days=1 )
task1 = dataObject.addTask()
task1.title = "Task 2"
task1.startDate = refDate + timedelta( hours=5 )
task1.dueDate   = task1.startDate + timedelta( hours=5 )

task1 = dataObject.addTask()
task1.title = "Task 3"
task1.startDate = refDate + timedelta( hours=8 )
task1.dueDate   = task1.startDate + timedelta( hours=5 )

task1 = dataObject.addTask()
task1.title = "Expired task 1"
task1.startDate = refDate - timedelta( days=2 )
task1.dueDate   = task1.startDate + timedelta( hours=5 )

task1 = dataObject.addTask()
task1.title = "Completed task 1"
task1.startDate = refDate - timedelta( days=2 )
task1.dueDate   = task1.startDate + timedelta( hours=5 )
task1.setCompleted()

recurrentTask = dataObject.addTask()
recurrentTask.title = "Recurrent task 1"
recurrentTask.dueDate = refDate.replace( day=20 ) + timedelta( hours=2 )
recurrentTask.recurrence = Recurrent()
recurrentTask.recurrence.setDaily()
recurrentTask.recurrence.endDate = recurrentTask.getReferenceDateTime().date() + timedelta( days=3 )

recurrentTask = dataObject.addTask()
recurrentTask.title = "Recurrent task 2"
recurrentTask.dueDate = refDate.replace( day=1, hour=22 )
recurrentTask.recurrence = Recurrent()
recurrentTask.recurrence.setWeekly()
recurrentTask.setCompleted()                ## mark first occurrence completed

calendar = MonthCalendar()
calendar.showCompletedTasks()
calendar.connectData( dataObject )
calendar.resize( 1024, 768 )
calendar.show()
# dialogCode = dialog.exec_()

# print( "Dialog return:", dialogCode )
# print( "Created todo:", dialog.todo )

sys.exit( app.exec_() )
