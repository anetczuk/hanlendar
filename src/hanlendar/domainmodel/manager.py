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
from typing import List

import glob

import icalendar

from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.task import Task, TaskOccurrence
from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.local.todo import LocalToDo
# from hanlendar import persist
# from hanlendar.domainmodel.item import Item
# from hanlendar.domainmodel.task import TaskOccurrence
# from hanlendar.domainmodel.local.todo import LocalToDo


_LOGGER = logging.getLogger(__name__)


## ======================================================


class Manager():
    """Root class for domain data structure."""

    @abc.abstractmethod
    def storeData( self ):
        """ retrun bool: True if new data saved, otherwise False """
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def loadData( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    ## ======================================================================

    def setData( self, manager: 'Manager' ):
        tasks = manager._getTasks()
        self._setTasks( tasks )
        todos = manager._getToDos()
        self._setToDos( todos )
        notes = manager._getNotes()
        self._setNotes( notes )

    @abc.abstractmethod
    def _getTasks( self ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def _setTasks( self, value ):
        raise NotImplementedError('You need to define this method in derived class!')

    @abc.abstractmethod
    def getTasksAll(self) -> List[Task]:
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
    def createEmptyToDo(self) -> LocalToDo:
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

    def findTaskByUID(self, uid) -> Task:
        allTasks = self.getTasksAll()
        for task in allTasks:
            if task.UID == uid:
                return task
        return None

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

    ### check if ancestor of task is added to root tasks
    def fixData(self):
        self.fixTaskParents()
        self.fixTaskRoots()
        self.fixTaskChildren()

    def fixTaskParents(self):
        rootTasks = self._getTasks()
        allTasks = self.getTasksAll()
        for task in allTasks:
            rootItem = task.getRootItem()
            if rootItem is None:
                continue
            if rootItem in rootTasks:
                continue
            ## invalid case -- root item not added to tasks
            _LOGGER.warning( "fixing task ancestor -- adding root task %s %s", rootItem.title, rootItem.UID )
            self.addTask( rootItem )

    def fixTaskRoots(self):
        rootTasks = self._getTasks()
        for index in range(len(rootTasks) - 1, -1, -1):
            task = rootTasks[ index ]
            if task.getParent() is not None:
                ## invalid case -- task with parent added to root tasks
                _LOGGER.warning( "fixing root tasks -- removing child %s %s", task.title, task.UID )
                del rootTasks[ index ]

    def fixTaskChildren(self):
        allTasks = self.getTasksAll()
        for task in allTasks:
            taskParent: Task = task.getParent()
            if taskParent is not None:
                subitems = taskParent.getSubitems()
                if task not in subitems:
                    ## invalid case
                    _LOGGER.warning( "task '%s' have invalid parent -- moved to task %s", task.title, taskParent.title )
                    task.setParent( taskParent )
            children = task.getSubitems()
            if children is None:
                continue
            for child in children:
                childParent = child.getParent()
                if childParent is not task:
                    ## invalid case
                    _LOGGER.warning( "task '%s' have invalid parent -- moved to task %s", child.title, task.title )
                    task.setParent( taskParent )

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

    def getNotificationList(self) -> List[ Notification ]:
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

    def insertToDo( self, todo: LocalToDo, todoCoords ):
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

    def addToDo( self, todo: LocalToDo = None ):
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

    def removeToDo( self, todo: LocalToDo ):
        return Item.removeSubItemFromList(self.todos, todo)

    def replaceToDo( self, oldToDo: LocalToDo, newToDo: LocalToDo ):
        return Item.replaceSubItemInList(self.todos, oldToDo, newToDo)

    def getNextToDo(self) -> LocalToDo:
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


def replace_in_list( aList, oldObject, newObject ):
    for i, _ in enumerate(aList):
        entry = aList[i]
        if entry == oldObject:
            aList[i] = newObject
            break
