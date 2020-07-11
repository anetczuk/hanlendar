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

from todocalendar import persist
from .task import Task
from .todo import ToDo
from .reminder import Notification


_LOGGER = logging.getLogger(__name__)


class Manager():
    """Root class for domain data structure."""

    _class_version = 0

    def __init__(self):
        """Constructor."""
        self.tasks = list()
        self.todos = list()
        self.notes = { "notes": "" }        ## default notes

    def store( self, outputDir ):
        outputFile = outputDir + "/version.obj"
        persist.storeObject( self._class_version, outputFile )

        outputFile = outputDir + "/tasks.obj"
        persist.storeObject( self.tasks, outputFile )

        outputFile = outputDir + "/todos.obj"
        persist.storeObject( self.todos, outputFile )

        outputFile = outputDir + "/notes.obj"
        persist.storeObject( self.notes, outputFile )

        self.backupData( outputDir )

    def load( self, inputDir ):
        inputFile = inputDir + "/version.obj"
        mngrVersion = persist.loadObject( inputFile )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        inputFile = inputDir + "/tasks.obj"
        self.tasks = persist.loadObject( inputFile )
        if self.tasks is None:
            self.tasks = list()

        inputFile = inputDir + "/todos.obj"
        self.todos = persist.loadObject( inputFile )
        if self.todos is None:
            self.todos = list()

        inputFile = inputDir + "/notes.obj"
        self.notes = persist.loadObject( inputFile )
        if self.notes is None:
            self.notes = { "notes": "" }

    def backupData(self, dataDir):
        objFiles = glob.glob( dataDir + "/*.obj" )
        storedZipFile = dataDir + "/data.zip"
        persist.backupFiles( objFiles, storedZipFile )

    def hasEntries( self, entriesDate: date ):
        for task in self.tasks:
            if task.hasEntryExact( entriesDate ):
                return True
        return False

    def getTasks( self ):
        return list( self.tasks )       ## shallow copy of list

    def getEntriesForDate(self, taskDate: date, includeCompleted=True):
        retList = list()
        for entry in self.tasks:
            if includeCompleted is False:
                if entry.isCompleted():
                    continue
            entry = entry.getEntryForDate( taskDate )
            if entry is not None:
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
            if task.dueDate is None:
                continue
            if retTask is None:
                retTask = task
            elif task.dueDate < retTask.dueDate:
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

    def addTask( self, task: Task ):
        self.tasks.append( task )

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
        replaceInList( self.tasks, oldTask, newTask )

    def addNewDeadline( self, eventdate: date, title ):
        event = Task()
        event.title = title
        event.setDeadlineDate( eventdate )
        self.addTask( event )

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

    def getToDos( self ):
        return list( self.todos )       ## shallow copy of list

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
        replaceInList( self.todos, oldToDo, newToDo )

    def getNextToDo(self) -> ToDo:
        tSize = len(self.todos)
        if tSize < 1:
            return None
        return self.todos[0]
    
    ## ========================================================

    def getNotes(self):
        return self.notes

    def setNotes(self, notesDict):
        self.notes = notesDict

    def importXfceNotes(self):
        newNotes = {}

        notes_dir = os.path.expanduser( "~/.local/share/notes" )
        for groupName in os.listdir( notes_dir ):
            group_dir = notes_dir + "/" + groupName
            for noteName in os.listdir( group_dir ):
                note_path = group_dir + "/" + noteName
                with open( note_path, 'r') as file:
                    data = file.read()
                    if noteName in newNotes:
                        ## the same note name in different groups -- append notes
                        newNotes[ noteName ] = newNotes[ noteName ] + "\n" + data
                    else:
                        newNotes[ noteName ] = data

        if len(newNotes) > 0:
            self.notes = newNotes

    def printTasks(self):
        retStr = ""
        tSize = len(self.tasks)
        for i in range(0, tSize):
            task = self.tasks[i]
            retStr += str(task) + "\n"
        return retStr


def replaceInList( aList, oldObject, newObject ):
    for i in range(0, len(aList)):
        entry = aList[i]
        if entry == oldObject:
            aList[i] = newObject
            break
