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
import pickle

from .task import Task
from .reminder import Notification


_LOGGER = logging.getLogger(__name__)


class Manager():
    """Root class for domain data structure."""

    def __init__(self):
        """Constructor."""
        self.tasks = list()
        self.notes = { "notes": "" }        ## default notes

    def store( self, outputDir ):
        outputTasksFile = outputDir + "/tasks.obj"
        _LOGGER.info( "saving tasks to: %s", outputTasksFile )
        with open(outputTasksFile, 'wb') as fp:
            pickle.dump( self.tasks, fp )

        outputNotesFile = outputDir + "/notes.obj"
        _LOGGER.info( "saving notes to: %s", outputNotesFile )
        with open(outputNotesFile, 'wb') as fp:
            pickle.dump( self.notes, fp )

    def load( self, inputDir ):
        try:
            inputTasksFile = inputDir + "/tasks.obj"
            _LOGGER.info( "loading tasks from: %s", inputTasksFile )
            with open( inputTasksFile, 'rb') as fp:
                self.tasks = pickle.load(fp)
        except FileNotFoundError:
            _LOGGER.exception("failed to load")
            self.tasks = list()
        except Exception:
            _LOGGER.exception("failed to load")
            raise

        try:
            inputNotesFile = inputDir + "/notes.obj"
            _LOGGER.info( "loading notes from: %s", inputNotesFile )
            with open( inputNotesFile, 'rb') as fp:
                self.notes = pickle.load(fp)
        except FileNotFoundError:
            _LOGGER.exception("failed to load")
            self.notes = { "notes": "" }        ## default notes
        except Exception:
            _LOGGER.exception("failed to load")
            raise

    def hasEntries( self, entriesDate: date ):
        for task in self.tasks:
            if task.hasEntry( entriesDate ):
                return True
        return False

#     def getEntries( self, entriesDate: date ):
#         retList = list()
#         for entry in self.tasks:
#             currDate = entry.getReferenceDateTime().date()
#             if currDate == entriesDate:
#                 retList.append( entry )
#         return retList

    def getTasks( self ):
        return list( self.tasks )       ## shallow copy of list

    def getNextDeadline(self) -> Task:
        tSize = len(self.tasks)
        if tSize < 1:
            return None
        retTask: Task = None
        for i in range(0, tSize):
            task = self.tasks[i]
            if task.isCompleted():
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
        for i in range(0, len(self.tasks)):
            entry = self.tasks[i]
            if entry == oldTask:
                self.tasks[i] = newTask
                break

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
