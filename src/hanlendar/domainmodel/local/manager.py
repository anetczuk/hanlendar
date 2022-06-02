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
from icalendar import cal

from hanlendar import persist
from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.local.task import Task, TaskOccurrence
from hanlendar.domainmodel.local.todo import ToDo


_LOGGER = logging.getLogger(__name__)



def extract_ical( content ):
    cal_begin_pos = content.find( "BEGIN:VCALENDAR" )
    if cal_begin_pos < 0:
        return content
    END_SUB = "END:VCALENDAR"
    cal_end_pos = content.find( END_SUB, cal_begin_pos )
    if cal_end_pos < 0:
        return content
    cal_end_pos += len( END_SUB )
    return content[ cal_begin_pos:cal_end_pos ]


def unpack_manager_module_mapper_v0( module ):
    ## convert from version 0 to actual version
    module = module.replace( "todocalendar", "hanlendar" )
    module = unpack_manager_module_mapper_v1( module )

def unpack_manager_module_mapper_v1( module ):
    ## convert from version 1 to actual version
    module = module.replace( "hanlendar.domainmodel.", "hanlendar.domainmodel.local." )
    return unpack_manager_module_mapper_v2( module )

def unpack_manager_module_mapper_v2( module ):
    ## convert from version 2 to actual version
    if module == "hanlendar.domainmodel.local.item":
        return "hanlendar.domainmodel.item"
    return unpack_manager_module_mapper_v3( module )

def unpack_manager_module_mapper_v3( module ):
    ## convert from version 3 to actual version
    if module == "hanlendar.domainmodel.local.recurrent":
        return "hanlendar.domainmodel.recurrent"
    if module == "hanlendar.domainmodel.local.reminder":
        return "hanlendar.domainmodel.reminder"
    return module


class LocalManager( Manager ):
    """Root class for domain data structure."""

    ## 1 - renamed modules from 'todocalendar' to 'hanlendar'
    ## 2 - renamed modules from 'hanlendar.domainmodel.*' to 'hanlendar.domainmodel.local.*'
    ## 3 - renamed modules from 'hanlendar.domainmodel.local.item' to 'hanlendar.domainmodel.item'
    ## 4 - renamed modules from 'hanlendar.domainmodel.local.recurrent' to 'hanlendar.domainmodel.recurrent'
    ##     renamed modules from 'hanlendar.domainmodel.local.reminder' to 'hanlendar.domainmodel.reminder'
    _class_version = 4

    def __init__(self, ioDir=None):
        """Constructor."""
        self._tasks = list()
        self._todos = list()
        self.notes = { "notes": "" }        ## default notes
        
        self._ioDir = ioDir                 ## do not persist

    def store( self, outputDir ):
        self._ioDir = outputDir
        self.store()

    def storeData( self ):
        outputDir = self._ioDir

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
        self._ioDir = inputDir
        self.loadData()

    def loadData( self ):
        inputDir = self._ioDir

        inputFile = inputDir + "/version.obj"
        mngrVersion = persist.load_object( inputFile )
        if mngrVersion != self. _class_version:
            _LOGGER.info( "converting object from version %s to %s", mngrVersion, self._class_version )
            ## do nothing for now

        module_mapper_dict = { 1: unpack_manager_module_mapper_v1,
                               2: unpack_manager_module_mapper_v2,
                               3: unpack_manager_module_mapper_v3 }
        if mngrVersion < 1:
            module_mapper = unpack_manager_module_mapper_v0
        else:
            module_mapper = module_mapper_dict.get( mngrVersion, None )

        inputFile = inputDir + "/tasks.obj"
        self.tasks = persist.load_object( inputFile, class_mapper=module_mapper )
        if self.tasks is None:
            self.tasks = list()

        inputFile = inputDir + "/todos.obj"
        self.todos = persist.load_object( inputFile, class_mapper=module_mapper )
        if self.todos is None:
            self.todos = list()

        inputFile = inputDir + "/notes.obj"
        self.notes = persist.load_object( inputFile, class_mapper=module_mapper )
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
    
    def importICalendar(self, content: str):
        try:
            extracted_ical = extract_ical( content )
            gcal = cal.Calendar.from_ical( extracted_ical )
            tasks = []
            for component in gcal.walk():
                if component.name == "VEVENT":
                    summary    = component.get('summary')
                    location   = component.get('location')
                    start_date = component.get('dtstart').dt
                    start_date = start_date.astimezone()            ## convert to local timezone
                    start_date = start_date.replace(tzinfo=None)
                    end_date   = component.get('dtend').dt
                    end_date   = end_date.astimezone()              ## convert to local timezone
                    end_date   = end_date.replace(tzinfo=None)
                    
                    #TODO: check if task already added
                    
                    task = Task()
                    task.title = f"{summary}, {location}"
                    task.description = component.get('description')
                    task.description = task.description.replace( "=0D=0A", "\n" )
                    task.startDateTime = start_date
                    task.dueDateTime   = end_date
                    task.addReminderDays( 1 )
                    
                    addedTask = self.addTask( task )
                    tasks.append( addedTask )
            return tasks
        except ValueError:
            _LOGGER.warning( "unable to import calendar data" )
        return None

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

    def renameNote(self, fromTitle, toTitle):
        self.notes[toTitle] = self.notes.pop(fromTitle)

    def removeNote(self, title):
        del self.notes[title]

    def printTasks(self):
        retStr = ""
        tSize = len(self.tasks)
        for i in range(0, tSize):
            task = self.tasks[i]
            retStr += str(task) + "\n"
        return retStr


## ========================================================


def replace_in_list( aList, oldObject, newObject ):
    for i, _ in enumerate(aList):
        entry = aList[i]
        if entry == oldObject:
            aList[i] = newObject
            break
