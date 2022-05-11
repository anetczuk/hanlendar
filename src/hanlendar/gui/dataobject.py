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

import os
import logging
from datetime import date

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QWidget, QUndoStack
from PyQt5.QtWidgets import QDialog

from hanlendar.gui.widget.taskdialog import TaskDialog
from hanlendar.gui.widget.tododialog import ToDoDialog

from hanlendar.gui.command.importxfcenotescommand import ImportXfceNotesCommand
from hanlendar.gui.command.importicalendarcommand import ImportICalendarCommand
from hanlendar.gui.command.addtaskcommand import AddTaskCommand
from hanlendar.gui.command.addsubtaskcommand import AddSubTaskCommand
from hanlendar.gui.command.edittaskcommand import EditTaskCommand
from hanlendar.gui.command.removetaskcommand import RemoveTaskCommand
from hanlendar.gui.command.marktaskcompletedcommand import MarkTaskCompletedCommand
from hanlendar.gui.command.movetaskcommand import MoveTaskCommand

from hanlendar.gui.command.addtodocommand import AddToDoCommand
from hanlendar.gui.command.addsubtodocommand import AddSubToDoCommand
from hanlendar.gui.command.edittodocommand import EditToDoCommand
from hanlendar.gui.command.removetodocommand import RemoveToDoCommand
from hanlendar.gui.command.marktodocompletedcommand import MarkToDoCompletedCommand
from hanlendar.gui.command.convertodototaskcommand import ConvertToDoToTaskCommand
from hanlendar.gui.command.movetodocommand import MoveToDoCommand

from hanlendar.gui.command.addnotecommand import AddNoteCommand
from hanlendar.gui.command.renamenotecommand import RenameNoteCommand
from hanlendar.gui.command.removenotecommand import RemoveNoteCommand

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.todo import ToDo


_LOGGER = logging.getLogger(__name__)


class DataObject( QObject ):

    ## added, modified or removed
    tasksChanged = pyqtSignal()
    ## added, modified or removed
    todosChanged = pyqtSignal()
    ## added, modified or removed
    notesChanged = pyqtSignal()

    def __init__(self, parent: QWidget=None):
        super().__init__( parent )

        self.parentWidget = parent
        self.domainModel = Manager()

        self.undoStack = QUndoStack(self)

    def getManager(self):
        return self.domainModel

    def load( self, inputDir ):
        self.domainModel.load( inputDir )

    def store( self, inputDir ):
        return self.domainModel.store( inputDir )

    def getTaskOccurrences(self, taskDate: date, includeCompleted=True):
        return self.domainModel.getTaskOccurrencesForDate( taskDate, includeCompleted )

    ## ==============================================================

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
        self.undoStack.push( AddSubTaskCommand( self, parent, task ) )

    def addTask(self, task: Task = None ) -> Task:
        if task is None:
            task = Task()
        self.undoStack.push( AddTaskCommand( self, task ) )
        return task

    def editTask(self, task: Task ):
        if task is None:
            return
        taskDialog = TaskDialog( task, self.parentWidget )
        taskDialog.setModal( True )
        dialogCode = taskDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.undoStack.push( EditTaskCommand( self, task, taskDialog.task ) )

    def removeTask(self, task: Task ):
        self.undoStack.push( RemoveTaskCommand( self, task ) )

    def markTaskCompleted(self, task: Task ):
        self.undoStack.push( MarkTaskCompletedCommand( self, task ) )

    def moveTask(self, taskCoords, parentTask, targetIndex):
        self.undoStack.push( MoveTaskCommand( self, taskCoords, parentTask, targetIndex ) )

    ## ==============================================================

    def addNewToDo( self, content=None ):
        todo = self._createToDo( content )
        self.addToDo( todo )

    def addToDo(self, todo: ToDo = None ) -> ToDo:
        if todo is None:
            todo = ToDo()
        self.undoStack.push( AddToDoCommand( self, todo ) )
        return todo

    def addNewSubToDo( self, parent: ToDo ):
        if parent is None:
            self.addNewToDo()
            return
        todo = self._createToDo()
        if todo is None:
            return
        self.undoStack.push( AddSubToDoCommand( self, parent, todo ) )

    def editToDo(self, todo: ToDo ):
        todoDialog = ToDoDialog( todo, self.parentWidget )
        todoDialog.setModal( True )
        dialogCode = todoDialog.exec_()
        if dialogCode == QDialog.Rejected:
            return
        self.undoStack.push( EditToDoCommand( self, todo, todoDialog.todo ) )

    def removeToDo(self, todo: ToDo ):
        self.undoStack.push( RemoveToDoCommand( self, todo ) )

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
        self.undoStack.push( ConvertToDoToTaskCommand( self, todo, taskDialog.task ) )

    def markToDoCompleted(self, todo: ToDo ):
        self.undoStack.push( MarkToDoCompletedCommand( self, todo ) )

    def moveToDo(self, todoCoords, parentToDo, targetIndex):
        self.undoStack.push( MoveToDoCommand( self, todoCoords, parentToDo, targetIndex ) )

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

    ## ==============================================================

    def addNote(self, title):
        self.undoStack.push( AddNoteCommand( self, title ) )

    def renameNote(self, fromTitle, toTitle):
        self.undoStack.push( RenameNoteCommand( self, fromTitle, toTitle ) )

    def removeNote(self, title):
        self.undoStack.push( RemoveNoteCommand( self, title ) )

    def importXfceNotes(self):
        newNotes = import_xfce_notes()
        if not newNotes:
            return
        self.undoStack.push( ImportXfceNotesCommand( self, newNotes ) )

    def importICalendar(self, file_path, silent=False):
        _LOGGER.info( "importing iCalendar from %s", file_path )
        with open( file_path, 'r' ) as cal_file:
            content = cal_file.read()
            self.undoStack.push( ImportICalendarCommand( self, content, silent ) )


def import_xfce_notes():
    newNotes = {}

    notesDir = os.path.expanduser( "~/.local/share/notes" )
    for groupName in os.listdir( notesDir ):
        groupDir = notesDir + "/" + groupName
        for noteName in os.listdir( groupDir ):
            notePath = groupDir + "/" + noteName
            with open( notePath, 'r') as file:
                data = file.read()
                if noteName in newNotes:
                    ## the same note name in different groups -- append notes
                    newNotes[ noteName ] = newNotes[ noteName ] + "\n" + data
                else:
                    newNotes[ noteName ] = data

    return newNotes
