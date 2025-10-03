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
except ImportError:
    ## when import fails then it means that the script was executed indirectly
    ## in this case __init__ is already loaded
    pass

import sys
from datetime import datetime, timedelta

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.dataobject import DataObject
from hanlendar.gui.widget.tasktable import TaskTable

from hanlendar.domainmodel.local.task import LocalTask


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

tasksList = []

task1 = LocalTask()
task1.title = "Task 1"
task1.description = "Description"
task1.completed = 50
task1.priority = 5
task1.setDefaultDateTime( datetime.today() )
tasksList.append( task1 )

task2 = LocalTask()
task2.title = "Task 2"
task2.description = "Description"
task2.completed = 0
task2.priority = 3
task2.setDefaultDateTime( datetime.today() + timedelta( hours=2 ) )
tasksList.append( task2 )

task = LocalTask()
task.title = "Default constructed task"
tasksList.append( task )

dataObject = DataObject()
manager = dataObject.getManager()
manager.tasks = tasksList

setup_interrupt_handling()

widget = TaskTable()
widget.resize( 1024, 768 )
widget.connectData( dataObject )
widget.show()

# print( "Dialog return:", dialogCode )
# print( "Created task:", dialog.task )

sys.exit( app.exec_() )
