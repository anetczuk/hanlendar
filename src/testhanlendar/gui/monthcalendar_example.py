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

import datetime
from datetime import timedelta

import hanlendar
import hanlendar.logger as logger
from hanlendar.gui.qt import QApplication, renderToPixmap
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.dataobject import DataObject
from hanlendar.gui.resources import get_root_path
from hanlendar.gui.widget.monthcalendar import MonthCalendar

from hanlendar.domainmodel.recurrent import Recurrent

from testhanlendar.mock_datetime import mock_datetime, mock_date


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


targetDate     = datetime.date(2020, 7, 16)
targetDatetime = datetime.datetime(2020, 7, 16)
mock_date( targetDate )
mock_datetime( targetDatetime )
mock_datetime( targetDatetime, hanlendar.domainmodel.task )


logFile = logger.get_logging_output_file()
logger.configure( logFile )

_LOGGER = logging.getLogger(__name__)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

setup_interrupt_handling()


dataObject = DataObject( None )

todayDate = datetime.datetime.today().replace( hour=6 )
task1 = dataObject.addTask()
task1.title = "Task 1"
task1.startDateTime = todayDate + timedelta( hours=5 )
task1.dueDateTime   = task1.startDateTime + timedelta( hours=5 )

refDate = todayDate + timedelta( days=1 )
task1 = dataObject.addTask()
task1.title = "Task 2"
task1.startDateTime = refDate + timedelta( hours=5 )
task1.dueDateTime   = task1.startDateTime + timedelta( hours=5 )

task1 = dataObject.addTask()
task1.title = "Task 3"
task1.startDateTime = refDate + timedelta( hours=8 )
task1.dueDateTime   = task1.startDateTime + timedelta( hours=5 )

task1 = dataObject.addTask()
task1.title = "Expired task 1"
task1.startDateTime = refDate - timedelta( days=2 )
task1.dueDateTime   = task1.startDateTime + timedelta( hours=5 )

task1 = dataObject.addTask()
task1.title = "Completed task 1"
task1.startDateTime = refDate - timedelta( days=2 )
task1.dueDateTime   = task1.startDateTime + timedelta( hours=5 )
task1.setCompleted()

recurrentTask = dataObject.addTask()
recurrentTask.title = "Recurrent task 1"
recurrentTask.dueDateTime = refDate.replace( day=20 ) + timedelta( hours=2 )
recurrentTask.recurrence = Recurrent()
recurrentTask.recurrence.setDaily()
recurrentTask.recurrence.endDate = recurrentTask.getReferenceInitDateTime().date() + timedelta( days=3 )

recurrentTask = dataObject.addTask()
recurrentTask.title = "Recurrent task 2"
recurrentTask.dueDateTime = refDate.replace( day=1, hour=22 )
recurrentTask.recurrence = Recurrent()
recurrentTask.recurrence.setWeekly()
recurrentTask.setCompleted()                ## mark first occurrence completed

calendar = MonthCalendar()
calendar.showCompletedTasks()
calendar.connectData( dataObject )
calendar.resize( 1024, 768 )
calendar.show()
# dialogCode = dialog.exec_()

root_path = get_root_path()
renderToPixmap( calendar, root_path + "/tmp/monthcalendar-big.png" )

# print( "Dialog return:", dialogCode )
# print( "Created todo:", dialog.todo )

sys.exit( app.exec_() )
