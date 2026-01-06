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

import logging
from typing import Any

import caldav
import icalendar

from hanlendar.domainmodel.manager import Manager

# from hanlendar.domainmodel.caldav.task import CalDAVTask
from hanlendar.domainmodel.local.manager import LocalManager
from hanlendar.domainmodel.icalio import import_icalendar, export_icalendar
from hanlendar.domainmodel.local.task import Task


_LOGGER = logging.getLogger(__name__)


class CalDAVConnector:

    def __init__(self):
        self._client = None
        self._principal = None
        self._calendarName: str = None
        self._calendar: caldav.objects.Calendar = None

    def getURL(self) -> str:
        if self._client is None:
            return None
        return self._client.url

    def getCalendarName(self) -> str:
        return self._calendarName

    def connectToServer(self, caldav_url, username, password):
        self._client = caldav.DAVClient(url=caldav_url, username=username, password=password)
        self._principal = self._client.principal()

    def connectToCalendar(self, calendar_name, *, allow_throw=False):
        if allow_throw is False:
            self._calendarName = calendar_name
            self._calendar = None
            self._calendar = self.getCalendar()
        else:
            self._calendar = self._initCalendar(calendar_name)

        if self._calendar is None:
            _LOGGER.warning("unable to connect to calendar '%s'", self._calendarName)
        else:
            _LOGGER.info("connected to calendar '%s' id: %s", self._calendar.name, self._calendar.id)

    def createCalendar(self, calendar_name=None) -> caldav.objects.Calendar:
        if calendar_name is not None:
            self._calendarName = calendar_name
        self._calendar = self._principal.make_calendar(name=self._calendarName)
        return self._calendar

    def deleteCalendar(self):
        self._calendar.delete()

    def getCalendar(self) -> caldav.objects.Calendar:
        if self._calendar is not None:
            return self._calendar
        try:
            return self._initCalendar(self._calendarName)
        except caldav.lib.error.NotFoundError as ex:
            _LOGGER.warning("unable to get calendar: %s", ex)
            return None

    def _initCalendar(self, calendar_name):
        self._calendarName = calendar_name
        self._calendar = None
        self._calendar = self._principal.calendar(name=self._calendarName)
        return self._calendar


class CalDAVManager(Manager):
    """Root class for domain data structure."""

    def __init__(self, connector, ioDir=None):
        self.calendar_id = None
        self._connector: CalDAVConnector = connector
        calendar = self._connector.getCalendar()
        if calendar is not None:
            self.calendar_id = calendar.id
        self._localManager = LocalManager(ioDir)
        self._localManager.setCalendarId(self.calendar_id)

    ## overriden
    def storeData(self) -> bool:
        _LOGGER.info("storing data")
        ret = self._localManager.storeData()
        self.saveToServer()
        return ret

    ## overriden
    def loadData(self):
        self.loadFromServer()
        self.fixData()

    def loadFromServer(self):
        server_url = self._connector.getURL()
        calendar_name = self._connector.getCalendarName()
        _LOGGER.info("loading calendar '%s' data from server %s", calendar_name, server_url)

        calendar: caldav.objects.Calendar = self._connector.getCalendar()
        if calendar is None:
            _LOGGER.warning("could not get CalDAV calendar")
            return

        self._localManager.tasks.clear()

        ### sync events
        all_events = calendar.events()
        dangling_children = []
        ## event: caldav.objects.Event = None
        for event in all_events:
            iCalendar: icalendar.cal.Calendar = event.icalendar_instance
            _item, children = import_icalendar(self._localManager, iCalendar)
            dangling_children.extend(children)

        fix_dangling_tasks(self._localManager, dangling_children)

        if len(dangling_children) > 0:
            _LOGGER.warning("not all children could be handled properly")
            _LOGGER.info("dangling children:")
            for item in dangling_children:
                child, parent_uuid = item
                _LOGGER.info("item: %s %s %s", child.UID, child.title, parent_uuid)
            _LOGGER.info("tasks:")
            for task in self._localManager.getTasksAll():
                _LOGGER.info("item: %s %s", task.UID, task.title)

    def saveToServer(self):
        _LOGGER.info("saving local data to server")

        calendar: caldav.objects.Calendar = None
        try:
            calendar = self._connector._initCalendar(self._connector._calendarName)
            ## erase calendar content
            # calendar.delete()

            for event_item in calendar.events():
                event_item.delete()
            for todo_item in calendar.todos():
                todo_item.delete()
            for journal_item in calendar.journals():
                journal_item.delete()

        except caldav.lib.error.NotFoundError as ex:
            _LOGGER.warning("unable to get calendar: %s", ex)
            calendar = self._connector.createCalendar()

        ical: icalendar.cal.Calendar = export_icalendar(self._localManager)
        ical_item: icalendar.cal.Calendar = None
        for component in ical.walk():
            if component.name == "VCALENDAR":
                ## skip
                continue
            if component.name == "VEVENT":
                ## caldav requires events to be wrapped in 'VCALENDAR' component
                ical_item = icalendar.cal.Calendar()
                ical_item.add_component(component)
                calendar.save_event(ical_item)
                continue
            if component.name == "VTODO":
                ## caldav requires events to be wrapped in 'VCALENDAR' component
                ical_item = icalendar.cal.Calendar()
                ical_item.add_component(component)
                calendar.save_event(ical_item)
                continue

            _LOGGER.warning("unhandled icalendar type: %s", component.name)

        _LOGGER.info("export done")

    ## ======================================================================

    ## overriden
    def _getUnknownProps(self) -> dict[Any, Any]:
        return self._localManager._getUnknownProps()

    # override
    def getCalendarId(self) -> str:
        return self.calendar_id

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
