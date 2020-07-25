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

from hanlendar.gui.qt import QApplication
from hanlendar.gui.sigint import setup_interrupt_handling
from hanlendar.gui.todotable import ToDoTable

from hanlendar.domainmodel.todo import ToDo


## ============================= main section ===================================


if __name__ != '__main__':
    sys.exit(0)


app = QApplication(sys.argv)
app.setApplicationName("Hanlendar")
app.setOrganizationName("arnet")
### app.setOrganizationDomain("www.my-org.com")

todosList = []
todo1 = ToDo()
todo1.title = "ToDo 1"
todo1.description = "Description"
todo1.completed = 50
todo1.priority = 5
todosList.append( todo1 )

todo2 = ToDo()
todo2.title = "ToDo 2"
todo2.description = "Description"
todo2.completed = 0
todo2.priority = 3
todosList.append( todo2 )

todo = ToDo()
todo.title = "ToDo 3"
todo.description = "Description"
todo.completed = 30
todo.priority = 11
todosList.append( todo )

todo = ToDo()
todo.title = "ToDo 4"
todo.description = "Description"
todo.completed = 0
todo.priority = 12
todosList.append( todo )

todo = ToDo()
todo.title = "Completed ToDo"
todo.description = "Description"
todo.completed = 100
todo.priority = 14
todosList.append( todo )

todo = ToDo()
todo.title = "ToDo Tree"
todo.description = "Description"
todo.completed = 0
todo.priority = 14
todosList.append( todo )

todoLeaf = ToDo()
todoLeaf.title = "ToDo Leaf 1"
todoLeaf.description = "Description"
todoLeaf.completed = 0
todoLeaf.priority = 16
todo.addSubtodo( todoLeaf )

todoLeaf = ToDo()
todoLeaf.title = "ToDo Leaf 2"
todoLeaf.description = "Description"
todoLeaf.completed = 0
todoLeaf.priority = 15
todoLeaf.addSubtodo( ToDo() ).title = "xxx"
todo.addSubtodo( todoLeaf )
# todo.subtodos.append( todoLeaf )

setup_interrupt_handling()

widget = ToDoTable()
widget.resize( 1024, 768 )
widget.setToDos( todosList )
widget.show()

# print( "Dialog return:", dialogCode )
# print( "Created task:", dialog.task )

sys.exit( app.exec_() )
