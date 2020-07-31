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

from datetime import date, datetime

import logging

import glob

from hanlendar import persist
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.todo import ToDo
from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.item import Item


_LOGGER = logging.getLogger(__name__)


class Manager():
    """Root class for domain data structure."""

    ## 1 - renamed modules
    _class_version = 1

    def __init__(self):
        """Constructor."""
        self._tasks = list()
        self._todos = list()
        self.notes = { "notes": "" }        ## default notes

    def store( self, outputDir ):
        outputFile = outputDir + "/version.obj"

        changed = False
        if persist.store_object( self._class_version, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/tasks.obj"
        if persist.store_object( self.tasks, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/todos.obj"
        if persist.store_object( self.todos, outputFile ) is True:
            changed = True

        outputFile = outputDir + "/notes.obj"
        if persist.store_object( self.notes, outputFile ) is True:
            changed = True

        ## backup data
        objFiles = glob.glob( outputDir + "/*.obj" )
        storedZipFile = outputDir + "/data.zip"
        persist.backup_files( objFiles, storedZipFile )

        return changed

    def load( self, inputDir ):
        inputFile = inputDir + "/version.obj"
        mngrVersion = persist.load_object( inputFile, self._class_version )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        inputFile = inputDir + "/tasks.obj"
        self.tasks = persist.load_object( inputFile, self._class_version )
        if self.tasks is None:
            self.tasks = list()

        inputFile = inputDir + "/todos.obj"
        self.todos = persist.load_object( inputFile, self._class_version )
        if self.todos is None:
            self.todos = list()

        inputFile = inputDir + "/notes.obj"
        self.notes = persist.load_object( inputFile, self._class_version )
        if self.notes is None:
            self.notes = { "notes": "" }

    ## ======================================================================

    @property
    def tasks(self):
        return self._tasks

    @tasks.setter
    def tasks(self, newList):
        self._tasks = newList

    def getTasks( self ):
        return list( self.tasks )                   ## shallow copy of list

    def getTasksAll(self):
        """Return tasks and all subtasks from tree."""
        return Item.getAllSubItemsFromList( self.tasks )

    def getTaskOccurrencesForDate(self, taskDate: date, includeCompleted=True):
        retList = list()
        allTasks = self.getTasksAll()
        for task in allTasks:
            entry = task.getTaskOccurrenceForDate( taskDate )
            if entry is None:
                continue
            if includeCompleted is False:
                if entry.isCompleted():
                    continue
            retList.append( entry )
        return retList

    def getNextDeadline(self) -> Task:
        retTask: Task = None
        allTasks = self.getTasksAll()
        for task in allTasks:
            if task.isCompleted():
                continue
            if task.occurrenceDue is None:
                continue
            if retTask is None:
                retTask = task
            elif task.occurrenceDue < retTask.occurrenceDue:
                retTask = task
        return retTask

    def getDeadlinedTasks(self):
        retTasks = list()
        allTasks = self.getTasksAll()
        for task in allTasks:
            if task.isCompleted():
                continue
            if task.isTimedout():
                retTasks.append( task )
        return retTasks

    def getRemindedTasks(self):
        retTasks = list()
        allTasks = self.getTasksAll()
        for task in allTasks:
            if task.isCompleted():
                continue
            if task.isReminded():
                retTasks.append( task )
        return retTasks

    def getTaskCoords(self, task):
        return Item.getItemCoords( self.tasks, task )

    def getTaskByCoords(self, task):
        return Item.getItemFromCoords( self.tasks, task )

    def insertTask( self, task: Task, taskCoords ):
        if taskCoords is None:
            self.tasks.append( task )
            return
        taskCoords = list( taskCoords )     ## make copy
        listPos = taskCoords.pop()
        parentTask = self.getTaskByCoords( taskCoords )
        if parentTask is not None:
            parentTask.addSubItem( task, listPos )
        else:
            self.tasks.insert( listPos, task )

    def addTask( self, task: Task = None ):
        if task is None:
            task = Task()
        self.tasks.append( task )
        task.setParent( None )
        return task

    def addNewTask( self, taskdate: date, title ):
        task = Task()
        task.title = title
        task.setDefaultDate( taskdate )
        self.addTask( task )
        return task

    def addNewTaskDateTime( self, taskdate: datetime, title ):
        task = Task()
        task.title = title
        task.setDefaultDateTime( taskdate )
        self.addTask( task )
        return task

    def removeTask( self, task: Task ):
        return Item.removeSubItemFromList(self.tasks, task)

    def replaceTask( self, oldTask: Task, newTask: Task ):
        return Item.replaceSubItemInList(self.tasks, oldTask, newTask)

    def addNewDeadlineDateTime( self, eventdate: datetime, title ):
        eventTask = Task()
        eventTask.title = title
        eventTask.setDeadlineDateTime( eventdate )
        self.addTask( eventTask )
        return eventTask

    def getNotificationList(self):
        ret = list()
        for i in range(0, len(self.tasks)):
            task = self.tasks[i]
            notifs = task.getNotifications()
            ret.extend( notifs )
        ret.sort( key=Notification.sortByTime )
        return ret

    ## ========================================================

    @property
    def todos(self):
        return self._todos

    @todos.setter
    def todos(self, newList):
        self._todos = newList

    def getToDos( self, includeCompleted=True ):
        if includeCompleted:
            return list( self.todos )       ## shallow copy of list
        return [ item for item in self.todos if not item.isCompleted() ]

    def getTodosAll(self):
        """Return todos and all subtodos from tree."""
        return Item.getAllSubItemsFromList( self.todos )

    def getToDoCoords(self, todo):
        return Item.getItemCoords( self.todos, todo )

    def getToDoByCoords(self, todo):
        return Item.getItemFromCoords( self.todos, todo )

    def insertToDo( self, todo: ToDo, todoCoords ):
        if todoCoords is None:
            self.todos.append( todo )
            return
        todoCoords = list( todoCoords )     ## make copy
        listPos = todoCoords.pop()
        parentToDo = self.getToDoByCoords( todoCoords )
        if parentToDo is not None:
            parentToDo.addSubItem( todo, listPos )
        else:
            self.todos.insert( listPos, todo )

    def addToDo( self, todo: ToDo = None ):
        if todo is None:
            todo = ToDo()
        self.todos.append( todo )
        todo.setParent( None )
        return todo

    def addNewToDo( self, title ):
        todo = ToDo()
        todo.title = title
        self.addToDo( todo )
        return todo

    def removeToDo( self, todo: ToDo ):
        return Item.removeSubItemFromList(self.todos, todo)

    def replaceToDo( self, oldToDo: ToDo, newToDo: ToDo ):
        return Item.replaceSubItemInList(self.todos, oldToDo, newToDo)

    def getNextToDo(self) -> ToDo:
        nextToDo = None
        allItems = self.getTodosAll()
        for item in allItems:
            if item.isCompleted():
                continue
            if nextToDo is None:
                nextToDo = item
                continue
            if nextToDo.priority < item.priority:
                nextToDo = item
        return nextToDo

    ## ========================================================

    def getNotes(self):
        return self.notes

    def setNotes(self, notesDict):
        self.notes = notesDict

    def addNote(self, title, content):
        self.notes[title] = content

    def printTasks(self):
        retStr = ""
        tSize = len(self.tasks)
        for i in range(0, tSize):
            task = self.tasks[i]
            retStr += str(task) + "\n"
        return retStr


def replace_in_list( aList, oldObject, newObject ):
    for i, _ in enumerate(aList):
        entry = aList[i]
        if entry == oldObject:
            aList[i] = newObject
            break
