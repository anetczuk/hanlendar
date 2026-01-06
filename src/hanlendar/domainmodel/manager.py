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
from typing import Any
import abc
from datetime import date, datetime

from hanlendar.domainmodel.reminder import Notification
from hanlendar.domainmodel.local.task import Task, LocalTask
from hanlendar.domainmodel.item import Item
from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.domainmodel.taskoccurrence import TaskOccurrence

# from hanlendar import persist
# from hanlendar.domainmodel.item import Item
# from hanlendar.domainmodel.local.todo import LocalToDo


_LOGGER = logging.getLogger(__name__)


## ======================================================


class Manager:
    """Root class for domain data structure."""

    @abc.abstractmethod
    def storeData(self) -> bool:
        """Return bool: True if new data saved, otherwise False."""
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def loadData(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    ## ======================================================================

    def setData(self, manager: "Manager"):
        tasks = manager._getTasks()
        self._setTasks(tasks)
        todos = manager._getToDos()
        self._setToDos(todos)
        notes = manager._getNotes()  # pylint: disable=W0212
        self._setNotes(notes)

    @abc.abstractmethod
    def _getUnknownProps(self) -> dict[Any, Any]:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @property
    def unknownProps(self) -> dict[Any, Any]:
        return self._getUnknownProps()

    @abc.abstractmethod
    def getCalendarId(self) -> str:
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _getTasks(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setTasks(self, _value):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def getTasksAll(self) -> list[Task]:
        """Return tasks and all subtasks from tree."""
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    ## return shallow copy (of list)
    def getTasks(self):
        tasksList = self._getTasks()
        return list(tasksList)

    @property
    def tasks(self):
        return self._getTasks()

    @tasks.setter
    def tasks(self, newList):
        self._setTasks(newList)

    @abc.abstractmethod
    def _getToDos(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setToDos(self, _value):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def getTodosAll(self):
        """Return tasks and all subtasks from tree."""
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    ## return shallow copy (of list)
    def getToDos(self, *, includeCompleted=True):
        if includeCompleted:
            return list(self.todos)  ## shallow copy of list
        return [item for item in self.todos if not item.isCompleted()]

    @property
    def todos(self):
        return self._getToDos()

    @todos.setter
    def todos(self, newList):
        self._setToDos(newList)

    @abc.abstractmethod
    def _getNotes(self):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    @abc.abstractmethod
    def _setNotes(self, _value):
        message = "You need to define this method in derived class!"
        raise NotImplementedError(message)

    def getNotes(self):
        return self._getNotes()

    def setNotes(self, notesDict):
        self._setNotes(notesDict)

    ## ======================================================================

    def findTaskByUID(self, uid) -> Task:
        allTasks = self.getTasksAll()
        for task in allTasks:
            if uid == task.UID:
                return task
        return None

    ## return TaskOccurrence list for given date
    def getTaskOccurrencesForDate(self, taskDate: date, *, includeCompleted=True) -> list[TaskOccurrence]:
        allTasks = self.getTasksAll()
        return Manager.getTaskOccurrencesForDateFromList(allTasks, taskDate, includeCompleted=includeCompleted)

    @staticmethod
    def getTaskOccurrencesForDateFromList(task_list, taskDate: date, *, includeCompleted=True) -> list[TaskOccurrence]:
        retList = []
        for task in task_list:
            entry = task.getTaskOccurrenceForDate(taskDate)
            if entry is None:
                continue
            if includeCompleted is False and entry.isCompleted():
                continue
            retList.append(entry)
        return retList

    def getNextDeadline(self) -> Task:
        allTasks = self.getTasksAll()
        return Manager.getNextDeadlineFromList(allTasks)

    @staticmethod
    def getNextDeadlineFromList(tasks_list) -> Task:
        retTask: Task = None
        for task in tasks_list:
            if task.isCompleted():
                continue
            if task.dueDateTime is None:
                continue
            if retTask is None or task.dueDateTime < retTask.dueDateTime:
                retTask = task
        return retTask

    def getDeadlinedTasks(self) -> list[Task]:
        allTasks = self.getTasksAll()
        return Manager.getDeadlinedTasksFromList(allTasks)

    @staticmethod
    def getDeadlinedTasksFromList(tasks_list) -> list[Task]:
        retTasks = []
        for task in tasks_list:
            occurrence: TaskOccurrence = task.currentOccurrence()
            if occurrence.isCompleted():
                continue
            if occurrence.isTimedout():
                retTasks.append(task)
        return retTasks

    def getRemindedTasks(self) -> list[Task]:
        allTasks = self.getTasksAll()
        return Manager.getRemindedTasksFromList(allTasks)

    @staticmethod
    def getRemindedTasksFromList(task_list) -> list[Task]:
        retTasks = []
        for task in task_list:
            occurrence: TaskOccurrence = task.currentOccurrence()
            if occurrence.isCompleted():
                continue
            if occurrence.isReminded():
                retTasks.append(task)
        return retTasks

    def getTaskCoords(self, task):
        return Item.getItemCoords(self.tasks, task)

    def getTaskByCoords(self, coords) -> Task:
        return Manager.getTaskByCoordsFromList(self.tasks, coords)

    @staticmethod
    def getTaskByCoordsFromList(task_list, coords) -> Task:
        return Item.getItemFromCoords(task_list, coords)

    def insertTask(self, task: Task, taskCoords):
        if taskCoords is None:
            self.tasks.append(task)
            return
        taskCoords = list(taskCoords)  ## make copy
        listPos = taskCoords.pop()
        parentTask = self.getTaskByCoords(taskCoords)
        if parentTask is not None:
            parentTask.addSubItem(task, listPos)
        else:
            self.tasks.insert(listPos, task)

    def addTask(self, task: Task = None) -> Task:
        if task is None:
            task = LocalTask()
            task.commonData.calendar_id = self.getCalendarId()
        self.tasks.append(task)
        task.setParent(None)
        return task

    def addNewTask(self, taskdate: date, title):
        task = LocalTask()
        task.commonData.calendar_id = self.getCalendarId()
        task.title = title
        task.setDefaultDate(taskdate)
        self.addTask(task)
        return task

    def addNewTaskDateTime(self, start_date: datetime, title) -> Task:
        task = LocalTask()
        task.commonData.calendar_id = self.getCalendarId()
        task.title = title
        task.setDefaultDateTime(start_date)
        self.addTask(task)
        return task

    def removeTask(self, task: Task) -> Task:
        return Item.removeSubItemFromList(self.tasks, task)

    def replaceTask(self, oldTask: Task, newTask: Task) -> bool:
        return Item.replaceSubItemInList(self.tasks, oldTask, newTask)

    ### check if ancestor of task is added to root tasks
    def fixData(self):
        self.fixTaskParents()
        self.fixTaskRoots()
        self.fixTaskChildren()

    def fixTaskParents(self):
        ## extract root tasks and add to top list
        rootTasks = self._getTasks()
        allTasks = self.getTasksAll()
        for task in allTasks:
            rootItem = task.getRootItem()
            if rootItem is None:
                continue
            if rootItem in rootTasks:
                continue
            ## invalid case -- root item not added to tasks
            _LOGGER.warning("fixing task ancestor -- adding root task %s %s", rootItem.title, rootItem.UID)
            self.addTask(rootItem)

    def fixTaskRoots(self):
        ## remove child tasks from root list
        rootTasks = self._getTasks()
        for index in range(len(rootTasks) - 1, -1, -1):
            task = rootTasks[index]
            if task.getParent() is not None:
                ## invalid case -- task with parent added to root tasks
                _LOGGER.warning("fixing root tasks -- removing child %s %s", task.title, task.UID)
                del rootTasks[index]

    def fixTaskChildren(self):
        allTasks = self.getTasksAll()
        for task in allTasks:
            taskParent: Task = task.getParent()
            if taskParent is not None:
                subitems = taskParent.getSubitems()
                if task not in subitems:
                    ## invalid case
                    _LOGGER.warning("task '%s' have invalid parent -- moved to task %s", task.title, taskParent.title)
                    task.setParent(taskParent)
            children = task.getSubitems()
            if children is None:
                continue
            for child in children:
                childParent = child.getParent()
                if childParent is not task:
                    ## invalid case
                    _LOGGER.warning("task '%s' have invalid parent -- moved to task %s", child.title, task.title)
                    task.setParent(taskParent)

    def printTasks(self):
        retStr = ""
        tSize = len(self.tasks)
        for i in range(tSize):
            task = self.tasks[i]
            retStr += str(task) + "\n"
        return retStr

    def addNewDeadlineDateTime(self, eventdate: datetime, title):
        eventTask = LocalTask()
        eventTask.commonData.calendar_id = self.getCalendarId()
        eventTask.title = title
        eventTask.setDeadlineDateTime(eventdate)
        self.addTask(eventTask)
        return eventTask

    def getNotificationList(self) -> list[Notification]:
        return Manager.getNotificationListFromList(self.tasks)

    @staticmethod
    def getNotificationListFromList(tasks_list) -> list[Notification]:
        ret = []
        for task in tasks_list:
            notifs = task.getNotifications()
            ret.extend(notifs)
        ret.sort(key=Notification.sortByTime)
        return ret

    ## ========================================================

    def getToDoCoords(self, todo: LocalToDo):
        return Item.getItemCoords(self.todos, todo)

    def getToDoByCoords(self, todoCoords) -> LocalToDo:
        return Manager.getToDoByCoordsFromList(self.todos, todoCoords)

    @staticmethod
    def getToDoByCoordsFromList(todo_list, coords) -> LocalToDo:
        return Item.getItemFromCoords(todo_list, coords)

    def insertToDo(self, todo: LocalToDo, todoCoords):
        if todoCoords is None:
            self.todos.append(todo)
            return
        todoCoords = list(todoCoords)  ## make copy
        listPos = todoCoords.pop()
        parentToDo = self.getToDoByCoords(todoCoords)
        if parentToDo is not None:
            parentToDo.addSubItem(todo, listPos)
        else:
            self.todos.insert(listPos, todo)

    def addToDo(self, todo: LocalToDo = None) -> LocalToDo:
        if todo is None:
            todo = LocalToDo()
            todo.commonData.calendar_id = self.getCalendarId()
        self.todos.append(todo)
        todo.setParent(None)
        return todo

    def addNewToDo(self, title: str) -> LocalToDo:
        todo = LocalToDo()
        todo.commonData.calendar_id = self.getCalendarId()
        todo.title = title
        self.addToDo(todo)
        return todo

    def removeToDo(self, todo: LocalToDo) -> LocalToDo:
        return Item.removeSubItemFromList(self.todos, todo)

    def replaceToDo(self, oldToDo: LocalToDo, newToDo: LocalToDo):
        return Item.replaceSubItemInList(self.todos, oldToDo, newToDo)

    def getNextToDo(self) -> LocalToDo:
        allItems = self.getTodosAll()
        return Manager.getNextToDoFromList(allItems)

    @staticmethod
    def getNextToDoFromList(todo_list) -> LocalToDo:
        nextToDo = None
        for item in todo_list:
            if item.isCompleted():
                continue
            if nextToDo is None:
                nextToDo = item
                continue
            if nextToDo.priority < item.priority:
                nextToDo = item
        return nextToDo

    ## ========================================================

    def addNote(self, title: str, content: str):
        notes = self._getNotes()
        notes[title] = content

    def renameNote(self, fromTitle: str, toTitle: str):
        notes = self._getNotes()
        notes[toTitle] = notes.pop(fromTitle)

    def removeNote(self, title: str):
        notes = self._getNotes()
        del notes[title]


## ========================================================


class MultiManager:

    def __init__(self, default_manager: Manager):
        self.enable_map: dict[str, bool] = {}  ## dict: calendar_id, is_enabled
        self.default_manager: Manager = default_manager
        self.manager_list: list[Manager] = []

    def setEnableMap(self, enable_map):
        if enable_map is None:
            self.enable_map = {}
            return
        self.enable_map = enable_map

    def getDefaultManager(self) -> Manager:
        return self.default_manager

    def getManagerById(self, calendar_id: str) -> Manager:
        for manager in self.manager_list:
            cal_id = manager.getCalendarId()
            if cal_id != calendar_id:
                continue
            return manager
        return self.default_manager

    def setManagerList(self, model_list: list[Manager]):
        self.manager_list = model_list
        self.manager_list.insert(0, self.default_manager)

    def loadData(self, custom_path=None):
        for manager in self.manager_list:
            if hasattr(manager, "loadFromDisk"):
                manager.loadFromDisk(custom_path)
            else:
                manager.loadData()

    def storeData(self, custom_path=None) -> bool:
        changed = False
        for manager in self.manager_list:
            if hasattr(manager, "storeToDisk"):
                if manager.storeToDisk(custom_path):
                    changed = True
            elif manager.storeData():
                changed = True
        return changed

    ## ======================================================================

    ## get all tasks (e.g. for task list table)
    ## it does not matter if any calendar is enabled or disabled - return all tasks for all managers
    def getTasks(self) -> list[Task]:
        ret_items = []
        for manager in self.manager_list:
            manager_items = manager.getTasks()
            if not manager_items:
                continue
            ret_items.extend(manager_items)
        return ret_items

    def addTask(self, task: Task = None) -> Task:
        cal_id = task.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.addTask(task)

    def insertTask(self, task: Task, taskCoords):
        cal_id = task.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.insertTask(task, taskCoords)

    def removeTask(self, task: Task):
        cal_id = task.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.removeTask(task)

    def replaceTask(self, oldTask: Task, newTask: Task) -> bool:
        old_cal_id = oldTask.commonData.calendar_id
        new_cal_id = newTask.commonData.calendar_id
        if new_cal_id == old_cal_id:
            manager = self.getManagerById(new_cal_id)
            return manager.replaceTask(oldTask, newTask)
        old_manager = self.getManagerById(old_cal_id)
        old_manager.removeTask(oldTask)
        new_manager = self.getManagerById(new_cal_id)
        new_manager.addTask(newTask)
        return True

    def getRemindedTasks(self) -> list[Task]:
        allTasks = self.getTasks()
        return Manager.getRemindedTasksFromList(allTasks)

    def getNextDeadline(self) -> Task:
        allTasks = self.getTasks()
        return Manager.getNextDeadlineFromList(allTasks)

    def getDeadlinedTasks(self) -> list[Task]:
        allTasks = self.getTasks()
        return Manager.getDeadlinedTasksFromList(allTasks)

    def getTaskCoords(self, task):
        cal_id = task.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.getTaskCoords(task)

    def getTaskByCoords(self, coords) -> Task:
        allTasks = self.getTasks()
        return Manager.getTaskByCoordsFromList(allTasks, coords)

    def getTaskOccurrencesForDate(self, taskDate: date, *, includeCompleted=True) -> list[TaskOccurrence]:
        allTasks = self.getTasks()
        return Manager.getTaskOccurrencesForDateFromList(allTasks, taskDate, includeCompleted=includeCompleted)

    def getNotificationList(self) -> list[Notification]:
        allTasks = self.getTasks()
        return Manager.getNotificationListFromList(allTasks)

    ## ======================================================================

    def getToDos(self):
        ret_items = []
        for manager in self.manager_list:
            manager_items = manager.todos
            if not manager_items:
                continue
            ret_items.extend(manager_items)
        return ret_items

    def addToDo(self, todo: LocalToDo) -> LocalToDo:
        cal_id = todo.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.addToDo(todo)

    def insertToDo(self, todo: LocalToDo, todoCoords):
        cal_id = todo.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        manager.insertToDo(todo, todoCoords)

    def removeToDo(self, todo: LocalToDo) -> LocalToDo:
        cal_id = todo.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.removeToDo(todo)

    def replaceToDo(self, oldToDo: LocalToDo, newToDo: LocalToDo):
        old_cal_id = oldToDo.commonData.calendar_id
        new_cal_id = newToDo.commonData.calendar_id
        if new_cal_id == old_cal_id:
            manager = self.getManagerById(new_cal_id)
            return manager.replaceToDo(oldToDo, newToDo)
        old_manager = self.getManagerById(old_cal_id)
        old_manager.removeToDo(oldToDo)
        new_manager = self.getManagerById(new_cal_id)
        new_manager.addToDo(newToDo)
        return True

    def getToDoByCoords(self, todoCoords) -> LocalToDo:
        allItems = self.getToDos()
        return Manager.getToDoByCoordsFromList(allItems, todoCoords)

    def getNextToDo(self) -> LocalToDo:
        allItems = self.getToDos()
        return Manager.getNextToDoFromList(allItems)

    def getToDoCoords(self, todo: LocalToDo):
        cal_id = todo.commonData.calendar_id
        manager = self.getManagerById(cal_id)
        return manager.getToDoCoords(todo)

    ## ======================================================================

    def getNotes(self):
        return self.default_manager.getNotes()

    def setNotes(self, notesDict):
        self.default_manager.setNotes(notesDict)

    def addNote(self, title: str, content: str):
        self.default_manager.addNote(title, content)

    def removeNote(self, title: str):
        self.default_manager.removeNote(title)

    def renameNote(self, from_title: str, to_title: str):
        self.default_manager.renameNote(from_title, to_title)


## ========================================================


def replace_in_list(aList, oldObject, newObject):
    for i, entry in enumerate(aList):
        if entry == oldObject:
            aList[i] = newObject
            break
