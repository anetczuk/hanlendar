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

# pylint: disable=W0212

import os
import logging
from typing import Any

import requests
import caldav
import icalendar

from hanlendar.domainmodel.manager import Manager

# from hanlendar.domainmodel.caldav.task import CalDAVTask
from hanlendar.domainmodel.local.manager import LocalManager
from hanlendar.domainmodel.icalio import import_icalendar, TaskSerialization, ToDoSerialization
from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.item import Item


_LOGGER = logging.getLogger(__name__)


class CalDAVConnector:

    def __init__(self, caldav_address: str, caldav_user: str, caldav_pass: str, caldav_calendar: str = None):
        self._caldav_address: str = caldav_address
        self._caldav_user: str = caldav_user
        self._caldav_pass: str = caldav_pass
        self._calendar_name: str = caldav_calendar

        self._client: caldav.DAVClient = None
        self._principal: caldav.Principal = None
        self._calendar: caldav.objects.Calendar = None

    def getURL(self) -> str:
        return self._caldav_address
        # return self._client.url

    def getCalendarName(self) -> str:
        return self._calendar_name

    def connectToServer(self, caldav_url: str = None, username: str = None, password: str = None) -> bool:
        if caldav_url:
            self._caldav_address = caldav_url
        if username:
            self._caldav_user = username
        if password:
            self._caldav_pass = password

        self._client = None
        self._principal = None

        try:
            self._client = caldav.DAVClient(
                url=self._caldav_address,
                username=self._caldav_user,
                password=self._caldav_pass,
            )
            self._principal = self._client.principal()
        except requests.exceptions.ConnectionError as ex:
            _LOGGER.warning("unable to connect: %s", ex)
            return False

        return True

    def connectToCalendar(self, calendar_name: str = None, *, allow_throw=False):
        if calendar_name is not None:
            self._calendar_name = calendar_name

        if allow_throw is False:
            self._calendar = None
            self._calendar = self.getCalendar()
        else:
            self._calendar = self._initCalendar()

        if self._calendar is None:
            _LOGGER.warning("unable to connect to calendar '%s'", self._calendar_name)
        else:
            _LOGGER.info("connected to calendar '%s' id: %s", self._calendar.name, self._calendar.id)

    def createCalendar(self, calendar_name: str = None) -> caldav.objects.Calendar:
        if calendar_name is not None:
            self._calendar_name = calendar_name
        if self._principal is None:
            return None
        self._calendar = self._principal.make_calendar(name=self._calendar_name)
        return self._calendar

    def deleteCalendar(self):
        self._calendar.delete()

    def getCalendar(self) -> caldav.objects.Calendar:
        if self._calendar is not None:
            return self._calendar
        try:
            return self._initCalendar()
        except caldav.lib.error.NotFoundError as ex:
            _LOGGER.warning("unable to get calendar: %s", ex)
            return None

    def _initCalendar(self) -> caldav.objects.Calendar:
        if self._principal is None:
            self.connectToServer()
        if self._principal is None:
            return None
        self._calendar = self._principal.calendar(name=self._calendar_name)
        return self._calendar


class CalDAVManager(Manager):
    """Root class for domain data structure."""

    def __init__(self, connector, ioDir: str = None):
        self._base_out_path: str = ioDir
        self._calendar_id: str = None
        self._connector: CalDAVConnector = connector

        ## editable local copy
        self._localManager = LocalManager(self._base_out_path)

        ## not modified recent copy from server
        ## serves to compare with "_localManager" to detect changes
        self._serverManager = LocalManager(self._base_out_path)

    ## overriden
    def storeData(self) -> bool:
        if self._calendar_id is None:
            _LOGGER.warning("unable to store data - no calendar id")
            return False
        _LOGGER.info(
            "storing calendar '%s' data",
            self._calendar_id,
        )
        self.saveToServer()
        ret1 = self._localManager.storeData()
        ret2 = self._serverManager.storeData()
        return ret1 and ret2

    def saveToServer(self):
        _LOGGER.info("saving local data to server")

        calendar: caldav.objects.Calendar = None
        try:
            calendar = self._connector._initCalendar()
            if calendar is None:
                calendar = self._connector.createCalendar()

        except caldav.lib.error.NotFoundError as ex:
            _LOGGER.warning("unable to get calendar: %s", ex)
            calendar = self._connector.createCalendar()

        except requests.exceptions.ConnectionError as ex:
            _LOGGER.warning("unable to store data - connection error: %s", ex)
            return

        if calendar is None:
            _LOGGER.warning("unable to store data - no calendar")
            return

        self.loadFromServer(save_cache_data=False)  ## download remote items

        server_url = self._connector.getURL()
        calendar_name = self._connector.getCalendarName()

        _LOGGER.info("exporting calendar '%s' data to server %s", calendar_name, server_url)
        self._saveTasks(calendar)
        self._saveToDos(calendar)

        _LOGGER.info("loading calendar '%s' data from server %s", calendar_name, server_url)
        self._loadFromCalendar(calendar, self._localManager)
        self._loadFromCalendar(calendar, self._serverManager)

    def _saveTasks(self, calendar: caldav.objects.Calendar):
        added_items, modified_items, deleted_items = self._get_tasks_changes()

        _LOGGER.info(
            "exporting new tasks: %s modified tasks: %s deleted tasks: %s",
            len(added_items),
            len(modified_items),
            len(deleted_items),
        )

        server_item: caldav.objects.Event = None

        ## handle deleted items
        for item in deleted_items:
            item_id = item.UID
            server_item = calendar.event_by_uid(item_id)  # type: ignore[assignment]
            if server_item is None:
                continue
            server_item.delete()

        ievent: icalendar.cal.Event = None

        ## handle modified items
        for item in modified_items:
            item_id = item.UID
            server_item = calendar.event_by_uid(item_id)  # type: ignore[assignment]
            if server_item is None:
                continue
            item.increaseSequence()  ## increase 'sequence' number
            ievent = TaskSerialization.to_ical(item)
            server_item.icalendar_component = ievent  # type: ignore[attr-defined]
            server_item.save(increase_seqno=False)  ## sequence already increased

        ## handle added items
        for item in added_items:
            ievent = TaskSerialization.to_ical(item)
            ical_item = icalendar.cal.Calendar()
            ical_item.add_component(ievent)
            calendar.save_event(ical_item)

    def _get_tasks_changes(self):
        server_items = self._serverManager.getTasksAll()
        local_items = self._localManager.getTasksAll()

        added_items = Item.get_added_items(server_items, local_items)
        modified_items = Item.get_modified_items(server_items, local_items)
        deleted_items = Item.get_deleted_items(server_items, local_items)

        return (added_items, modified_items, deleted_items)

    def _saveToDos(self, calendar: caldav.objects.Calendar):
        added_items, modified_items, deleted_items = self._get_todos_changes()

        _LOGGER.info(
            "exporting new todos: %s modified todos: %s deleted todos: %s",
            len(added_items),
            len(modified_items),
            len(deleted_items),
        )

        server_item: caldav.objects.Todo = None

        ## handle deleted items
        for item in deleted_items:
            item_id = item.UID
            server_item = calendar.todo_by_uid(item_id)  # type: ignore[assignment]
            if server_item is None:
                continue
            server_item.delete()

        ievent: icalendar.cal.Todo = None

        ## handle modified items
        for item in modified_items:
            item_id = item.UID
            server_item = calendar.todo_by_uid(item_id)  # type: ignore[assignment]
            if server_item is None:
                continue
            item.increaseSequence()  ## increase 'sequence' number
            ievent = ToDoSerialization.to_ical(item)
            server_item.icalendar_component = ievent  # type: ignore[attr-defined]
            server_item.save(increase_seqno=False)  ## sequence already increased

        ## handle added items
        for item in added_items:
            ievent = ToDoSerialization.to_ical(item)
            ical_item = icalendar.cal.Calendar()
            ical_item.add_component(ievent)
            calendar.save_event(ical_item)

    def _get_todos_changes(self):
        server_items = self._serverManager.getTodosAll()
        local_items = self._localManager.getTodosAll()

        added_items = Item.get_added_items(server_items, local_items)
        modified_items = Item.get_modified_items(server_items, local_items)
        deleted_items = Item.get_deleted_items(server_items, local_items)

        return (added_items, modified_items, deleted_items)

    ## overriden
    def loadData(self):
        if self._calendar_id is None:
            _LOGGER.warning("unable to load data - no calendar id")
            return
        self.loadDataLocal()
        self.loadFromServer()

    ## load data from local storage only (do not perform any connection)
    # override
    def loadDataLocal(self):
        if self._calendar_id is None:
            _LOGGER.warning("unable to load data - no calendar id")
            return
        self._serverManager.loadData()
        self._localManager.loadData()

    def loadFromServer(self, *, save_cache_data: bool = True):
        server_url = self._connector.getURL()
        calendar_name = self._connector.getCalendarName()
        _LOGGER.info("loading calendar '%s' data from server %s", calendar_name, server_url)

        calendar: caldav.objects.Calendar = self._connector.getCalendar()
        if calendar is None:
            _LOGGER.warning("could not get CalDAV calendar")
            return

        added_tasks, modified_tasks, deleted_tasks = self._get_tasks_changes()
        _LOGGER.info(
            "local not exported tasks: %s modified tasks: %s deleted tasks: %s",
            len(added_tasks),
            len(modified_tasks),
            len(deleted_tasks),
        )

        added_todos, modified_todos, deleted_todos = self._get_todos_changes()
        _LOGGER.info(
            "local not exported todos: %s modified todos: %s deleted todos: %s",
            len(added_todos),
            len(modified_todos),
            len(deleted_todos),
        )

        self._loadFromCalendar(calendar, self._serverManager)
        self._loadFromCalendar(calendar, self._localManager)

        _LOGGER.info("imported tasks: %s todos: %s", len(self._localManager.tasks), len(self._localManager.todos))

        ## apply local changes to new content from server

        ## apply tasks local changes
        for item in deleted_tasks:
            item_id = item.UID
            old_task = self._localManager.findTaskByUID(item_id)
            if old_task is None:
                _LOGGER.warning("unable to find task: %s", item_id)
                continue
            self._localManager.removeTask(old_task)

        for item in modified_tasks:
            item_id = item.UID
            old_task = self._localManager.findTaskByUID(item_id)
            if old_task is None:
                _LOGGER.warning("unable to find task: %s", item_id)
                continue
            old_task.updateData(item)  # type: ignore[attr-defined]

        for item in added_tasks:
            self._localManager.addTask(item)

        ## apply todos local changes
        for item in deleted_todos:
            item_id = item.UID
            old_todo = self._localManager.findTodoByUID(item_id)
            if old_todo is None:
                _LOGGER.warning("unable to find todo: %s", item_id)
                continue
            self._localManager.removeToDo(old_todo)

        for item in modified_todos:
            item_id = item.UID
            old_todo = self._localManager.findTodoByUID(item_id)
            if old_todo is None:
                _LOGGER.warning("unable to find todo: %s", item_id)
                continue
            old_todo.updateData(item)

        for item in added_todos:
            self._localManager.addToDo(item)

        self._localManager.fixData()

        _LOGGER.info("all tasks: %s todos: %s", len(self._localManager.tasks), len(self._localManager.todos))

        if save_cache_data:
            self._serverManager.storeData()
            self._localManager.storeData()

    def _loadFromCalendar(self, calendar: caldav.objects.Calendar, manager: LocalManager):
        self._loadTasks(calendar, manager)
        self._loadToDos(calendar, manager)
        manager.fixData()

    def _loadTasks(self, calendar: caldav.objects.Calendar, manager: LocalManager):
        manager.tasks.clear()

        ### sync events
        all_events = calendar.events()
        dangling_children = []
        ## event: caldav.objects.Event = None
        for event in all_events:
            iCalendar: icalendar.cal.Calendar = event.icalendar_instance
            _item, children = import_icalendar(manager, iCalendar)
            dangling_children.extend(children)

        fix_dangling_tasks(manager, dangling_children)

        if len(dangling_children) > 0:
            _LOGGER.warning("not all children could be handled properly")
            _LOGGER.info("dangling children:")
            for item in dangling_children:
                child, parent_uuid = item
                _LOGGER.info("item: %s %s %s", child.UID, child.title, parent_uuid)
            _LOGGER.info("tasks:")
            for task in manager.getTasksAll():
                _LOGGER.info("item: %s %s", task.UID, task.title)

    def _loadToDos(self, calendar: caldav.objects.Calendar, manager: LocalManager):
        pass

    ## overriden
    def synchronize_data(self):
        self.loadFromServer()

    ## ======================================================================

    ## overriden
    def _getUnknownProps(self) -> dict[Any, Any]:
        return self._localManager._getUnknownProps()

    # override
    def getCalendarId(self) -> str:
        return self._calendar_id

    def setCalendarId(self, calendar_id: str):
        self._calendar_id = calendar_id
        self._set_output_dir(self._localManager, "local")
        self._set_output_dir(self._serverManager, "remote")

    def _set_output_dir(self, manager: LocalManager, suffix: str):
        manager.setCalendarId(self._calendar_id)
        if self._base_out_path is None:
            return
        manager._ioDir = os.path.join(self._base_out_path, f"{self._calendar_id}_{suffix}")

    # override
    def _getTasks(self):
        return self._localManager._getTasks()

    # override
    def _setTasks(self, value):
        self._localManager._setTasks(value)

    ## overriden
    def getTasksAll(self):
        return self._localManager.getTasksAll()

    ## overriden
    def _getToDos(self):
        return self._localManager._getToDos()

    ## overriden
    def _setToDos(self, value):
        self._localManager._setToDos(value)

    ## overriden
    def getTodosAll(self):
        return self._localManager.getTodosAll()

    ## overriden
    def _getNotes(self):
        return self._localManager._getNotes()

    ## overriden
    def _setNotes(self, value):
        self._localManager._setNotes(value)


## ================================================================


def fix_dangling_tasks(manager: Manager, dangling_children):
    ## handle dangling children
    while len(dangling_children) > 0:
        handled = False
        for i in range(len(dangling_children) - 1, -1, -1):
            child, parent_uid = dangling_children[i]
            taskParent: Task = manager.findTaskByUID(parent_uid)
            if taskParent is not None:
                ## add as subitem
                taskParent.addSubItem(child)
                del dangling_children[i]
                handled = True
        if handled is True:
            continue

        #         _LOGGER.warning( "not all children could be handled properly" )
        #
        #         print( "dangling children:" )
        #         for item in dangling_children:
        #             child, parent_uuid = item
        #             print( "item:", child.UID, parent_uuid )
        #         print( "tasks:" )
        #         for item in manager.getTasksAll():
        #             print( "item:", item.UID )

        ## add remaining dangling children as regular tasks
        for item in dangling_children:
            child, _other = item
            manager.addTask(child)
        break
