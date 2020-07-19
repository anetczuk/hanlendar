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
from datetime import date, datetime

import logging

import glob

from hanlendar import persist
from .task import Task
from .todo import ToDo
from .reminder import Notification


_LOGGER = logging.getLogger(__name__)


class Manager():
    """Root class for domain data structure."""

    ## 1 - renamed modules
    _class_version = 1

    def __init__(self):
        """Constructor."""
        self.tasks = list()
        self.todos = list()
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

    def getTasks( self ):
        return list( self.tasks )       ## shallow copy of list

    def getTaskOccurrencesForDate(self, taskDate: date, includeCompleted=True):
        retList = list()
        for task in self.tasks:
            entry = task.getTaskOccurrenceForDate( taskDate )
            if entry is None:
                continue
            if includeCompleted is False:
                if entry.isCompleted():
                    continue
            retList.append( entry )
        return retList

    def getNextDeadline(self) -> Task:
        tSize = len(self.tasks)
        if tSize < 1:
            return None
        retTask: Task = None
        for i in range(0, tSize):
            task = self.tasks[i]
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
        tSize = len(self.tasks)
        if tSize < 1:
            return list()
        retTasks = list()
        for i in range(0, tSize):
            task = self.tasks[i]
            if task.isCompleted():
                continue
            if task.isTimedout():
                retTasks.append( task )
        return retTasks

    def getRemindedTasks(self):
        tSize = len(self.tasks)
        if tSize < 1:
            return list()
        retTasks = list()
        for i in range(0, tSize):
            task = self.tasks[i]
            if task.isCompleted():
                continue
            if task.isReminded():
                retTasks.append( task )
        return retTasks

    def addTask( self, task: Task = None ):
        if task is None:
            task = Task()
        self.tasks.append( task )
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
        self.tasks.remove( task )

    def replaceTask( self, oldTask: Task, newTask: Task ):
        replace_in_list( self.tasks, oldTask, newTask )

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

    def getToDos( self, includeCompleted=True ):
        if includeCompleted:
            return list( self.todos )       ## shallow copy of list
        return [ item for item in self.todos if not item.isCompleted() ]

    def addToDo( self, todo: ToDo ):
        self.todos.append( todo )

    def addNewToDo( self, title ):
        todo = ToDo()
        todo.title = title
        self.addToDo( todo )
        return todo

    def removeToDo( self, todo: ToDo ):
        self.todos.remove( todo )

    def replaceToDo( self, oldToDo: ToDo, newToDo: ToDo ):
        replace_in_list( self.todos, oldToDo, newToDo )

    def getNextToDo(self) -> ToDo:
        tSize = len(self.todos)
        nextToDo = None
        for i in range(0, tSize):
            todo = self.todos[i]
            if todo.isCompleted():
                continue
            if nextToDo is None:
                nextToDo = todo
                continue
            if nextToDo.priority < todo.priority:
                nextToDo = todo
        return nextToDo

    def setToDoPriorityLeast(self, todo: ToDo):
        if len(self.todos) < 1:
            return
        sortedTodos = self.getToDos(False)
        sortedTodos.remove( todo )
        sortedTodos.sort( key=ToDo.sortByPriority )         ## ascending
        smallestPriority = sortedTodos[0].priority
        if smallestPriority > todo.priority:
            ## "todo" item has smallest priority and there is no other todos with the same priority
            return
        smallestPriority -= 1
        if smallestPriority < 0:
            todo.priority = 0
            priorValue = abs( smallestPriority )
            for item in sortedTodos:
                item.priority += priorValue
        else:
            todo.priority = smallestPriority

    def setToDoPriorityRaise(self, todo: ToDo, newPriority):
        todo.priority = newPriority
        sortedTodos = self.getToDos(False)
        sortedTodos.remove( todo )
        sortedTodos.sort( key=ToDo.sortByPriority )         ## ascending
        prevPriority = newPriority
        for item in sortedTodos:
            if item.priority < newPriority:
                continue
            if item.priority > prevPriority:
                break
            item.priority += 1
            prevPriority = item.priority

    def setToDoPriorityDecline(self, todo: ToDo, newPriority):
        todo.priority = newPriority
        sortedTodos = self.getToDos(False)
        sortedTodos.remove( todo )
        sortedTodos.sort( key=ToDo.sortByPriority, reverse=True )         ## descending
        prevPriority = newPriority
        for item in sortedTodos:
            if item.priority > newPriority:
                continue
            if item.priority < prevPriority:
                break
            item.priority -= 1
            prevPriority = item.priority

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
