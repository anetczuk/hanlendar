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


from todocalendar.gui.qt import QApplication
from todocalendar.gui.sigint import setup_interrupt_handling
from todocalendar.gui.todotable import ToDoTable

from todocalendar.domainmodel.todo import ToDo


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

todo1 = ToDo()
todo1.title = "ToDo 1"
todo1.description = "Description"
todo1.completed = 50
todo1.priority = 5

todo2 = ToDo()
todo2.title = "ToDo 2"
todo2.description = "Description"
todo2.completed = 0
todo2.priority = 3

setup_interrupt_handling()

widget = ToDoTable()
widget.setToDos( [todo1, todo2] )
widget.show()

# print( "Dialog return:", dialogCode )
# print( "Created task:", dialog.task )

sys.exit( app.exec_() )
