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

import abc

import glob
from icalendar import cal
from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.item import Item
import icalendar
from hanlendar.domainmodel.local.todo import ToDo

# from hanlendar import persist
# from hanlendar.domainmodel.item import Item
# from hanlendar.domainmodel.task import TaskOccurrence
# from hanlendar.domainmodel.local.todo import ToDo


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


## ======================================================


class Manager():
    """Root class for domain data structure."""

    @abc.abstractmethod
    def storeData( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def loadData( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    ## ======================================================================
    
    @abc.abstractmethod
    def _getTasks( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setTasks( self, value ):
        raise NotImplementedError('You need to define this method in derived class!')
 
    @abc.abstractmethod
    def getTasksAll(self):
        """Return tasks and all subtasks from tree."""
        raise NotImplementedError('You need to define this method in derived class!')

    ## return shallow copy (of list)
    def getTasks( self ):
        tasksList = self._getTasks()
        return list( tasksList )
 
    @property
    def tasks(self):
        return self._getTasks()

    @tasks.setter
    def tasks(self, newList):
        self._setTasks( newList )

    @abc.abstractmethod
    def createEmptyTask(self) -> Task:
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _getToDos( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setToDos( self, value ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getTodosAll(self):
        """Return tasks and all subtasks from tree."""
        raise NotImplementedError('You need to define this method in derived class!')
 
    ## return shallow copy (of list)
    def getToDos( self, includeCompleted=True ):
        if includeCompleted:
            return list( self.todos )       ## shallow copy of list
        return [ item for item in self.todos if not item.isCompleted() ]

    @property
    def todos(self):
        return self._getToDos()

    @todos.setter
    def todos(self, newList):
        self._setToDos( newList )

    @abc.abstractmethod
    def createEmptyToDo(self) -> ToDo:
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _getNotes( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setNotes( self, value ):
        raise NotImplementedError('You need to define this method in derived class!')

    def getNotes(self):
        return self._getNotes()

    def setNotes(self, notesDict):
        self._setNotes( notesDict )

    ## ======================================================================
 
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
            occurrence: TaskOccurrence = task.currentOccurrence()
            if occurrence.isCompleted():
                continue
            if occurrence.isTimedout():
                retTasks.append( task )
        return retTasks
 
    def getRemindedTasks(self):
        retTasks = list()
        allTasks = self.getTasksAll()
        for task in allTasks:
            occurrence: TaskOccurrence = task.currentOccurrence()
            if occurrence.isCompleted():
                continue
            if occurrence.isReminded():
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
            task = self.createEmptyTask()
        self.tasks.append( task )
        task.setParent( None )
        return task

    def addNewTask( self, taskdate: date, title ):
        task = self.createEmptyTask()
        task.title = title
        task.setDefaultDate( taskdate )
        self.addTask( task )
        return task

    def addNewTaskDateTime( self, taskdate: datetime, title ):
        task = self.createEmptyTask()
        task.title = title
        task.setDefaultDateTime( taskdate )
        self.addTask( task )
        return task

    def removeTask( self, task: Task ):
        return Item.removeSubItemFromList(self.tasks, task)

    def replaceTask( self, oldTask: Task, newTask: Task ):
        return Item.replaceSubItemInList(self.tasks, oldTask, newTask)
 
    def printTasks(self):
        retStr = ""
        tSize = len(self.tasks)
        for i in range(0, tSize):
            task = self.tasks[i]
            retStr += str(task) + "\n"
        return retStr
 
    def addNewDeadlineDateTime( self, eventdate: datetime, title ):
        eventTask = self.createEmptyTask()
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
            todo = self.createEmptyToDo()
        self.todos.append( todo )
        todo.setParent( None )
        return todo
 
    def addNewToDo( self, title ):
        todo = self.createEmptyToDo()
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
 
    def addNote(self, title, content):
        notes = self._getNotes()
        notes[title] = content
 
    def renameNote(self, fromTitle, toTitle):
        notes = self._getNotes()
        notes[toTitle] = notes.pop(fromTitle)
 
    def removeNote(self, title):
        notes = self._getNotes()
        del notes[title]

    ## ========================================================

    def importICalendar(self, content: str):
        try:
            extracted_ical = extract_ical( content )
            calendar: icalendar.cal.Calendar = cal.Calendar.from_ical( extracted_ical )
            return self.importICalendarObject( calendar )
        except ValueError as ex:
            _LOGGER.warning( "unable to import calendar data: %s", ex )
        return None

    def importICalendarObject(self, calendar: icalendar.cal.Calendar):
        tasks = []
        for component in calendar.walk():
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
                
                task = self.createEmptyTask()
                task.title = f"{summary}, {location}"
                task.description = component.get('description')
                if task.description is None:
                    task.description = ""
                task.description = task.description.replace( "=0D=0A", "\n" )
                task.startDateTime = start_date
                task.dueDateTime   = end_date
                task.addReminderDays( 1 )
                
                addedTask = self.addTask( task )
                tasks.append( addedTask )
        return tasks


## ========================================================


def replace_in_list( aList, oldObject, newObject ):
    for i, _ in enumerate(aList):
        entry = aList[i]
        if entry == oldObject:
            aList[i] = newObject
            break
