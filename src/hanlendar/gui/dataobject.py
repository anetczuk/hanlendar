# MIT License
#
# Copyright (c) 2020 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

import logging
from datetime import date

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QDialog, QMessageBox

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import Task
from hanlendar.gui.taskdialog import TaskDialog
from hanlendar.domainmodel.todo import ToDo
from hanlendar.gui.tododialog import ToDoDialog


# _LOGGER = logging.getLogger(__name__)


class DataObject( QObject ):

    ## added, modified or removed
    taskChanged = pyqtSignal( Task )
    ## added, modified or removed
    todoChanged = pyqtSignal( ToDo )

    def __init__(self, parent: QWidget):
        super().__init__( parent )

        self.parentWidget = parent
        self.domainModel = Manager()

    def getManager(self):
        return self.domainModel

    def load( self, inputDir ):
        self.domainModel.load( inputDir )

    def store( self, inputDir ):
        self.domainModel.store( inputDir )

    def getEntries(self, taskDate: date, includeCompleted=True):
        return self.domainModel.getEntriesForDate( taskDate, includeCompleted )

    ## ==============================================================

    def addNewTask( self, newTaskDate: QDate = None ):
        task = Task()
        if newTaskDate is not None:
            startDate = newTaskDate.toPyDate()
            task.setDefaultDate( startDate )

        taskDialog = TaskDialog( task, self.parentWidget )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.addTask( taskDialog.task )

    def addTask(self, task: Task = None ) -> Task:
        if task is None:
            task = Task()
        self.domainModel.addTask( task )
        self.taskChanged.emit( task )
        return task

    def editTask(self, task: Task ):
        if task is None:
            return
        taskDialog = TaskDialog( task, self.parentWidget )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.replaceTask( task, taskDialog.task )
        self.taskChanged.emit( taskDialog.task )

    def removeTask(self, task: Task ):
        self.domainModel.removeTask( task )
        self.taskChanged.emit( task )

    def markTaskCompleted(self, task: Task ):
        task.setCompleted()
        self.taskChanged.emit( task )

    ## ==============================================================

    def addNewToDo( self ):
        todo = ToDo()
        todoDialog = ToDoDialog( todo, self.parentWidget )
        todoDialog.setModal( True )
        dialogCode = todoDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.addToDo( todoDialog.todo )
        self.todoChanged.emit( todoDialog.todo )

    def editToDo(self, todo: ToDo ):
        todoDialog = ToDoDialog( todo, self.parentWidget )
        todoDialog.setModal( True )
        dialogCode = todoDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.replaceToDo( todo, todoDialog.todo )
        self.todoChanged.emit( todoDialog.todo )

    def removeToDo(self, todo: ToDo ):
        self.domainModel.removeToDo( todo )
        self.todoChanged.emit( todo )

    def convertToDoToTask(self, todo: ToDo ):
        task = Task()
        task.title       = todo.title
        task.description = todo.description
        task._completed  = todo._completed
        task.priority    = todo.priority

        taskDialog = TaskDialog( task, self.parentWidget )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.addTask( taskDialog.task )
        self.removeToDo( todo )

    def markToDoCompleted(self, todo: ToDo ):
        todo.setCompleted()
        self.todoChanged.emit( todo )
