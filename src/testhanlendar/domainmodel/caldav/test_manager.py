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

import unittest

import time
import datetime
import requests

from hanlendar.domainmodel.caldav.manager import CalDAVManager, CalDAVConnector
from hanlendar.domainmodel.icalio import replace_line

from testhanlendar.data import get_data_path
from testhanlendar.domainmodel.caldav.radicalemock import RadicaleLocalServer


class CalDAVManagerTest(unittest.TestCase):

    RADICALE_USER = "bob"

    def setUp(self):
        ## Called before testfunction is executed
        config_path = get_data_path("radicale.cfg")
        self.radicale_server = RadicaleLocalServer(config_path, remove_storage=True)
        self.radicale_server.start()

        self.connector = self._connect()
        self.assertTrue(self.connector is not None)

        calendar = self.connector.createCalendar(calendar_name="test_calendar")
        self.calendar_uuid = calendar.id
        calendars_num = self.radicale_server.count_calendars(self.RADICALE_USER)
        self.assertEqual(calendars_num, 1)

        self.manager = CalDAVManager(self.connector)

    def _connect(self) -> CalDAVConnector:
        local_address = self.radicale_server.get_local_address()
        for _i in range(100):
            try:
                connector = CalDAVConnector(f"http://{local_address}", self.RADICALE_USER, "bob")
                if connector.connectToServer() is False:
                    time.sleep(0.01)  ## sleep a bit to allow server startup
                    continue
            # ruff: noqa: PERF203
            except requests.exceptions.ConnectionError:
                time.sleep(0.01)  ## sleep a bit to allow server startup
                continue
            else:
                return connector
        return None

    def tearDown(self):
        ## Called after testfunction was executed
        self.radicale_server.stop()

    def test_addTask(self):
        taskDate = datetime.datetime(2025, 11, 22, 10, 20, 30)
        new_task = self.manager.addNewTaskDateTime(taskDate, "task1")
        new_task.UID = "1111-2222-3333-4444"
        new_task._common_data.createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        new_task._common_data.lastModifiedDate = datetime.datetime(2025, 11, 23, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        self.manager.saveToServer()

        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 1)

        content = self.radicale_server.get_item(new_task.UID)
        # replace 'now()' time with constant
        content = replace_line(content, "DTSTAMP:", "20251121T092030Z")
        self.assertEqual(
            """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PYVOBJECT//NONSGML Version 1//EN
BEGIN:VEVENT
UID:1111-2222-3333-4444
DTSTART:20251122T092030Z
DTEND:20251122T102030Z
CREATED:20251122T092030Z
DTSTAMP:20251121T092030Z
LAST-MODIFIED:20251123T092030Z
SUMMARY:task1
END:VEVENT
END:VCALENDAR
""",
            content,
        )

    def test_addTodo(self):
        new_todo = self.manager.addNewToDo("todo1")
        new_todo.UID = "1111-2222-3333-4444"
        new_todo._common_data.createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # pylint: disable=W0212
        self.manager.saveToServer()

        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 1)

        content = self.radicale_server.get_item(new_todo.UID)
        # replace 'now()' time with constant
        content = replace_line(content, "DTSTAMP:", "20251110T152141Z")
        content = replace_line(content, "LAST-MODIFIED:", "20251110T152241Z")
        self.assertEqual(
            """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PYVOBJECT//NONSGML Version 1//EN
BEGIN:VTODO
CREATED:20251122T092030Z
DTSTAMP:20251110T152141Z
LAST-MODIFIED:20251110T152241Z
SUMMARY:todo1
UID:1111-2222-3333-4444
END:VTODO
END:VCALENDAR
""",
            content,
        )

    def test_save_new(self):
        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 0)

        ## add new task
        taskDate = datetime.datetime(2025, 11, 22, 10, 20, 30)
        new_task = self.manager.addNewTaskDateTime(taskDate, "task1")
        new_task.UID = "1111-2222-3333-4444"
        new_task._common_data.createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        new_task._common_data.lastModifiedDate = datetime.datetime(2025, 11, 23, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        self.manager.saveToServer()

        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 1)

    def test_save_modify(self):
        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 0)

        ## add new task
        taskDate = datetime.datetime(2025, 11, 22, 10, 20, 30)
        new_task = self.manager.addNewTaskDateTime(taskDate, "task1")
        new_task.UID = "1111-2222-3333-4444"
        new_task._common_data.createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        new_task._common_data.lastModifiedDate = datetime.datetime(2025, 11, 23, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        self.manager.saveToServer()
        self.assertEqual(new_task.sequence, 0)

        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 1)

        ## modify task
        new_task = self.manager.findTaskInstance(new_task)
        modified_title = new_task.title + "_xxx"
        new_task.title = modified_title
        self.manager.saveToServer()

        ## check change
        manager = CalDAVManager(self.connector)
        manager.loadFromServer()
        self.assertEqual(len(manager.tasks), 1)
        loaded_task = manager.tasks[0]
        self.assertEqual(loaded_task.title, modified_title)
        self.assertEqual(loaded_task.sequence, 1)

    def test_save_delete(self):
        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 0)

        ## add new task
        taskDate = datetime.datetime(2025, 11, 22, 10, 20, 30)
        new_task = self.manager.addNewTaskDateTime(taskDate, "task1")
        new_task.UID = "1111-2222-3333-4444"
        new_task._common_data.createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        new_task._common_data.lastModifiedDate = datetime.datetime(2025, 11, 23, 9, 20, 30)  # type: ignore[attr-defined] # pylint: disable=W0212
        self.manager.saveToServer()

        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 1)

        ## remove task
        new_task = self.manager.findTaskInstance(new_task)
        self.manager.removeTask(new_task)
        self.manager.saveToServer()

        ## check change
        calendar_items_num = self.radicale_server.count_calendar_items(self.RADICALE_USER, self.calendar_uuid)
        self.assertEqual(calendar_items_num, 0)
