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
from PyQt5.QtWidgets import QDialog

from hanlendar.gui.widget.taskdialog import TaskDialog
from hanlendar.gui.widget.tododialog import ToDoDialog

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.todo import ToDo


_LOGGER = logging.getLogger(__name__)


class DataObject( QObject ):

    ## added, modified or removed
    taskChanged = pyqtSignal()
    ## added, modified or removed
    todoChanged = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super().__init__( parent )

        self.parentWidget = parent
        self.domainModel = Manager()

    def getManager(self):
        return self.domainModel

    def load( self, inputDir ):
        self.domainModel.load( inputDir )

    def store( self, inputDir ):
        return self.domainModel.store( inputDir )

    def getTaskOccurrences(self, taskDate: date, includeCompleted=True):
        return self.domainModel.getTaskOccurrencesForDate( taskDate, includeCompleted )

    ## ==============================================================

    def setTasksList(self, newList):
        self.getManager().tasks = newList
        self.taskChanged.emit()

    def addNewTask( self, newTaskDate: QDate = None ):
        task = self._createTask( newTaskDate )
        if task is None:
            return
        self.addTask( task )

    def addNewSubTask( self, parent: Task ):
        if parent is None:
            self.addNewTask()
            return
        task = self._createTask()
        if task is None:
            return
        parent.addSubItem( task )
        self.taskChanged.emit()

    def addTask(self, task: Task = None ) -> Task:
        if task is None:
            task = Task()
        self.domainModel.addTask( task )
        self.taskChanged.emit()
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
        self.taskChanged.emit()

    def removeTask(self, task: Task ):
        removed = self.domainModel.removeTask( task )
        if removed is None:
            _LOGGER.warning( "unable to remove task: %s", task )
        self.taskChanged.emit()

    def markTaskCompleted(self, task: Task ):
        task.setCompleted()
        self.taskChanged.emit()

    ## ==============================================================

    def setTodosList(self, newList):
        self.getManager().todos = newList
        self.todoChanged.emit()

    def addNewToDo( self, content=None ):
        todo = self._createToDo( content )
        if todo is None:
            return
        self.domainModel.addToDo( todo )
        self.todoChanged.emit()

    def addNewSubToDo( self, parent: ToDo ):
        if parent is None:
            self.addNewToDo()
            return
        todo = self._createToDo()
        if todo is None:
            return
        parent.addSubItem( todo )
        self.todoChanged.emit()

    def editToDo(self, todo: ToDo ):
        todoDialog = ToDoDialog( todo, self.parentWidget )
        todoDialog.setModal( True )
        dialogCode = todoDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.domainModel.replaceToDo( todo, todoDialog.todo )
        self.todoChanged.emit()

    def removeToDo(self, todo: ToDo ):
        removed = self.domainModel.removeToDo( todo )
        if removed is None:
            _LOGGER.warning( "unable to remove todo: %s", todo )
        self.todoChanged.emit()

    def convertToDoToTask(self, todo: ToDo ):
        task = Task()
        task.title       = todo.title
        task.description = todo.description
        task.completed   = todo.completed
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
        self.todoChanged.emit()

    def _createTask( self, newTaskDate: QDate = None ):
        task = Task()
        if newTaskDate is not None:
            startDate = newTaskDate.toPyDate()
            task.setDefaultDate( startDate )

        taskDialog = TaskDialog( task, self.parentWidget )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return None
        return taskDialog.task

    def _createToDo( self, content=None ):
        todo = ToDo()
        if content is not None:
            todo.description = content
        todoDialog = ToDoDialog( todo, self.parentWidget )
        todoDialog.setModal( True )
        dialogCode = todoDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return None
        return todoDialog.todo
