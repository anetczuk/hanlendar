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
import caldav
import icalendar
import requests

from hanlendar.domainmodel.manager import Manager
from hanlendar.domainmodel.item import Item
# from hanlendar.domainmodel.caldav.task import CalDAVTask
from hanlendar.domainmodel.local.manager import LocalManager
from hanlendar.domainmodel.task import Task
from hanlendar.domainmodel.icalio import import_icalendar, export_icalendar, \
    fix_dangling_tasks
# from hanlendar import persist
# from hanlendar.domainmodel.reminder import Notification
# from hanlendar.domainmodel.task import TaskOccurrence
# from hanlendar.domainmodel.local.todo import LocalToDo


_LOGGER = logging.getLogger(__name__)


class CalDAVConnector():

    def __init__(self):
        self._client                            = None
        self._principal                         = None
        self._calendarName: str                 = None
        self._calendar: caldav.objects.Calendar = None

    def connectToServer(self, caldav_url, username, password ):
        self._client = caldav.DAVClient( url=caldav_url, username=username, password=password )
#         self._client.headers[ "Connection" ] = "Keep-Alive"
#         self._client.headers[ "Keep-Alive" ] = "timeout=60, max=1000"

    def connectToCalendar(self, calendar_name, allow_throw=False):
        if allow_throw is False:
            self._calendarName = calendar_name
            self._calendar     = None
            self._calendar     = self.getCalendar()
        else:
            self._calendar = self._initCalendar( calendar_name )

    def createCalendar( self, calendar_name=None ) -> caldav.objects.Calendar:
        if calendar_name is not None:
            self._calendarName = calendar_name
        self._calendar = self._principal.make_calendar( name=self._calendarName )
        return self._calendar

    def deleteCalendar(self):
        self._calendar.delete()

    def getCalendar(self) -> caldav.objects.Calendar:
        if self._calendar is not None:
            return self._calendar
        try:
            return self._initCalendar( self._calendarName )
        except caldav.lib.error.NotFoundError as ex:
            _LOGGER.warning( "unable to get calendar: %s", ex )
            return None

    def _initCalendar(self, calendar_name ):
        self._calendarName = calendar_name
        self._calendar     = None
        self._principal = self._client.principal()
        self._calendar  = self._principal.calendar( name=self._calendarName )
        return self._calendar


class CalDAVManager( Manager ):
    """Root class for domain data structure."""

    def __init__(self, connector, ioDir=None):
        """Constructor."""
        self._connector: CalDAVConnector = connector
        self._localManager = LocalManager( ioDir )

    ## overriden
    def storeData( self ):
        ret = self._localManager.storeData()
        self.saveToServer()
        return ret

    ## overriden
    def loadData( self ):
        self.loadFromServer()
        self.fixData()
#         self._localManager.storeData()

    def loadFromServer(self):
        _LOGGER.info( "loading data from server" )

        calendar: caldav.objects.Calendar = self._connector.getCalendar()
        if calendar is None:
            return

        self._localManager.tasks.clear()

        ### sync events
        all_events = calendar.events()
        dangling_children = []
        ## event: caldav.objects.Event = None
        for event in all_events:
            iCalendar: icalendar.cal.Calendar = event.icalendar_instance
            _, children = import_icalendar( self._localManager, iCalendar )
            dangling_children.extend( children )

        fix_dangling_tasks( self._localManager, dangling_children )

        if len( dangling_children ) > 0:
            _LOGGER.warning( "not all children could be handled properly" )
            print( "dangling children:" )
            for item in dangling_children:
                child, parent_uuid = item
                print( "item:", child.UID, child.title, parent_uuid )
            print( "tasks:" )
            for task in self._localManager.getTasksAll():
                print( "item:", task.UID, task.title )

    def saveToServer(self):
        _LOGGER.info( "saving local data to server" )

        calendar: caldav.objects.Calendar = None
        try:
            calendar = self._connector._initCalendar( self._connector._calendarName )
            calendar.delete()
        except caldav.lib.error.NotFoundError as ex:
            _LOGGER.warning( "unable to get calendar: %s", ex )
            calendar = None

        _LOGGER.info( "creating calendar: %s", self._connector._calendarName )
        newCalendar: caldav.objects.Calendar = self._connector.createCalendar()

        ical: icalendar.cal.Calendar = export_icalendar( self._localManager )
        for component in ical.walk():
            if component.name == "VEVENT":
                ## caldav requires events to be wrapped in 'VCALENDAR' component
                calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
                calendar.add_component( component )
                newCalendar.save_event( calendar )

        _LOGGER.info( "export done" )

    ## ======================================================================

    # override
    def _getTasks( self ):
        return self._localManager._getTasks()

    # override
    def _setTasks( self, value ):
        self._localManager._setTasks( value )

    ## overriden
    def getTasksAll(self):
        return self._localManager.getTasksAll()

    # override
    def createEmptyTask(self):
        return self._localManager.createEmptyTask()

    ## overriden
    def _getToDos( self ):
        return self._localManager._getToDos()

    ## overriden
    def _setToDos( self, value ):
        self._localManager._setToDos( value )

    ## overriden
    def getTodosAll(self):
        return self._localManager.getTodosAll()

    # override
    def createEmptyToDo(self):
        return self._localManager.createEmptyToDo()

    ## overriden
    def _getNotes( self ):
        return self._localManager._getNotes()

    ## overriden
    def _setNotes( self, value ):
        self._localManager._setNotes( value )
