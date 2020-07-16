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
from datetime import datetime, timedelta


#### append local library
sys.path.append(os.path.abspath( os.path.join(os.path.dirname(__file__), "../..") ))


from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.daylistwidget import DayListWidget

from hanlendar.domainmodel.task import Task


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

taskDate = datetime.today()

task1 = Task()
task1.title = "Task 1"
task1.description = "Description"
task1.completed = 50
task1.priority = 5
task1.setDefaultDateTime( taskDate )

task2 = Task()
task2.title = "Task 2"
task2.description = "Description"
task2.completed = 0
task2.priority = 3
task2.setDefaultDateTime( taskDate + timedelta( hours=2 ) )

task3 = Task()
task3.title = "Full Day Task"
task3.description = "Description"
task3.completed = 0
task3.priority = 3
task3.startDate = taskDate         - timedelta( days=2 )
task3.dueDate   = task3.startDate  + timedelta( days=4 )

setup_interrupt_handling()

widget = DayListWidget()
widget.resize( 800, 600 )
widget.setTasks( [task1, task2, task3], taskDate.date() )
widget.show()

# print( "Dialog return:", dialogCode )
# print( "Created task:", dialog.task )

sys.exit( app.exec_() )
