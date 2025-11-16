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

import datetime
from datetime import timedelta
import icalendar

from hanlendar.domainmodel import icalio
from hanlendar.domainmodel.icalio import (
    import_icalendar_content,
    export_icalendar_content,
    timedelta_from_string,
    sort_ical_content,
    replace_line,
    remove_line,
)

from hanlendar.domainmodel.recurrent import Recurrent, RepeatType
from hanlendar.domainmodel.local.manager import LocalManager as Manager
from hanlendar.domainmodel.local.task import LocalTask
from hanlendar.domainmodel.reminder import Reminder
from hanlendar.domainmodel.local.todo import LocalToDo
from hanlendar.domainmodel.caldav.manager import fix_dangling_tasks

from testhanlendar.data import get_data_path
from testhanlendar.domainmodel.caldav.radicalemock import read_file


class ICalIOTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        self.maxDiff = None

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_sort_ical_list_001(self):
        content = """\
BEGIN:AAA2
bbb
aaa
END:AAA2
BEGIN:AAA1
ddd
ccc
END:AAA1
"""
        sorted_content = sort_ical_content(content)
        self.assertEqual(
            """\
BEGIN:AAA1
ccc
ddd
END:AAA1
BEGIN:AAA2
aaa
bbb
END:AAA2
""",
            sorted_content,
        )

    def test_sort_ical_list_002(self):
        content = """\
BEGIN:AAA
BEGIN:AAA
ddd
ccc
END:AAA
bbb
aaa
END:AAA
"""
        sorted_content = sort_ical_content(content)
        self.assertEqual(
            """\
BEGIN:AAA
aaa
bbb
BEGIN:AAA
ccc
ddd
END:AAA
END:AAA
""",
            sorted_content,
        )

    def test_importICalendar(self):
        manager = Manager()

        content = """
BEGIN:VCALENDAR
PRODID:-//Flo Inc.//FloSoft//EN
BEGIN:VEVENT
DTSTART:20220414T132000Z
DTEND:20220414T134000Z
UID:1234__4321
LOCATION:Remiza Warszawska 123
DESCRIPTION;ENCODING=QUOTED-PRINTABLE:Zapraszamy na wizytę.=0D=0AŻyczymy miłego dnia.
SUMMARY:Umówiona wizyta
PRIORITY:3
END:VEVENT
END:VCALENDAR
"""

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 0)

        import_icalendar_content(manager, content)

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 1)

        calTask = tasks[0]
        self.assertEqual(calTask.UID, "1234__4321")
        self.assertEqual(calTask.title, "Umówiona wizyta")
        self.assertEqual(calTask.location, "Remiza Warszawska 123")
        self.assertEqual(calTask.startDateTime.replace(tzinfo=None), datetime.datetime(2022, 4, 14, 15, 20))
        self.assertEqual(calTask.dueDateTime.replace(tzinfo=None), datetime.datetime(2022, 4, 14, 15, 40))

    def test_importICalendar_eml(self):
        manager = Manager()

        #         with open( "/tmp/test.eml", 'r' ) as cal_file:
        #             content = cal_file.read()

        content = """
X-Account-Key: account3
X-Mozilla-Status: 0001
X-Mozilla-Status2: 00000000

BEGIN:VCALENDAR
PRODID:-//Flo Inc.//FloSoft//EN
BEGIN:VEVENT
DTSTART:20220414T132000Z
DTEND:20220414T134000Z
UID:1234__4321
LOCATION:Remiza Warszawska 123
DESCRIPTION;ENCODING=QUOTED-PRINTABLE:Zapraszamy na wizytę.=0D=0AŻyczymy miłego dnia.
SUMMARY:Umówiona wizyta
PRIORITY:3
END:VEVENT
END:VCALENDAR


"""

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 0)

        import_icalendar_content(manager, content)

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 1)

        calTask = tasks[0]
        self.assertEqual(calTask.UID, "1234__4321")
        self.assertEqual(calTask.title, "Umówiona wizyta")
        self.assertEqual(calTask.location, "Remiza Warszawska 123")
        self.assertEqual(calTask.startDateTime.replace(tzinfo=None), datetime.datetime(2022, 4, 14, 15, 20))
        self.assertEqual(calTask.dueDateTime.replace(tzinfo=None), datetime.datetime(2022, 4, 14, 15, 40))

    def test_importICalendar_completed(self):
        manager = Manager()

        content = """
BEGIN:VCALENDAR
PRODID:-//Flo Inc.//FloSoft//EN
BEGIN:VEVENT
DTSTART:20220414T132000Z
DTEND:20220414T134000Z
UID:1234__4321
LOCATION:Remiza Warszawska 123
DESCRIPTION;ENCODING=QUOTED-PRINTABLE:Zapraszamy na wizytę.=0D=0AŻyczymy miłego dnia.
SUMMARY:Umówiona wizyta
PRIORITY:3
X-HANLENDAR-COMPLETEDX:100
END:VEVENT
END:VCALENDAR
"""

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 0)

        import_icalendar_content(manager, content)

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 1)

        calTask = tasks[0]
        self.assertEqual(calTask.UID, "1234__4321")
        self.assertEqual(calTask.title, "Umówiona wizyta")
        self.assertEqual(calTask.location, "Remiza Warszawska 123")
        self.assertEqual(calTask.startDateTime.replace(tzinfo=None), datetime.datetime(2022, 4, 14, 15, 20))
        self.assertEqual(calTask.dueDateTime.replace(tzinfo=None), datetime.datetime(2022, 4, 14, 15, 40))
        self.assertEqual(calTask.completed, 100)

    def test_importICalendar_subitems_reverse(self):
        manager = Manager()

        content = """
BEGIN:VCALENDAR
BEGIN:VEVENT
SUMMARY:a subtitle example
UID:1212afc7-09c2-4ee5-88f6-2829e247e9d6@hanlendar
DESCRIPTION:
X-HANLENDAR-COMPLETEDX:0
X-HANLENDAR-PARENT:284cd1d8-701a-4bea-8603-3cf4dd9a1260@hanlendar
X-HANLENDAR-RECCUR-OFFSET:0
END:VEVENT
BEGIN:VEVENT
SUMMARY:title example
UID:284cd1d8-701a-4bea-8603-3cf4dd9a1260@hanlendar
DESCRIPTION:
X-HANLENDAR-COMPLETEDX:0
X-HANLENDAR-RECCUR-OFFSET:0
END:VEVENT
END:VCALENDAR
"""

        tasks = manager.getTasksAll()
        self.assertEqual(len(tasks), 0)

        _item, dangling_children = import_icalendar_content(manager, content)
        fix_dangling_tasks(manager, dangling_children)

        newTasks = manager.getTasksAll()
        self.assertEqual(len(newTasks), 2)

        newTask: LocalTask = newTasks[0]
        self.assertEqual(newTask.UID, "284cd1d8-701a-4bea-8603-3cf4dd9a1260@hanlendar")
        self.assertEqual(newTask.title, "title example")
        newSubTask: LocalTask = newTasks[1]
        self.assertEqual(newSubTask.UID, "1212afc7-09c2-4ee5-88f6-2829e247e9d6@hanlendar")
        self.assertEqual(newSubTask.title, "a subtitle example")
        self.assertEqual(newSubTask.getParent(), newTask)

    ## ===================================================================

    def test_io_list(self):
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
        ievent = icalendar.cal.Event()
        event_data_list = [1, 2, 4, 3]
        icalio.set_ical_list(ievent, "XXX", event_data_list)
        calendar.add_component(ievent)
        calendar_string = calendar.to_ical()
        calendar_string = calendar_string.decode("utf-8")

        calendar = icalendar.cal.Calendar.from_ical(calendar_string)
        events = calendar.walk("VEVENT")
        event = events[0]
        data_list = icalio.get_ical_list(event, "XXX")

        self.assertEqual(data_list, ["1", "2", "4", "3"])

    def test_io_list_comma(self):
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
        ievent = icalendar.cal.Event()
        event_data_list = ["1,11", "2,22", "3,33", "4,44"]
        icalio.set_ical_list(ievent, "XXX", event_data_list)
        calendar.add_component(ievent)
        calendar_string = calendar.to_ical()
        calendar_string = calendar_string.decode("utf-8")

        calendar = icalendar.cal.Calendar.from_ical(calendar_string)
        events = calendar.walk("VEVENT")
        event = events[0]
        data_list = icalio.get_ical_list(event, "XXX")

        self.assertEqual(data_list, event_data_list)

    def test_io_dict(self):
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
        ievent = icalendar.cal.Event()
        event_data_dict = {"aaa": "1", "bbb": "2"}
        icalio.set_ical_dict(ievent, "XXX", 5, event_data_dict)
        calendar.add_component(ievent)
        calendar_string = calendar.to_ical()
        calendar_string = calendar_string.decode("utf-8")

        calendar = icalendar.cal.Calendar.from_ical(calendar_string)
        events = calendar.walk("VEVENT")
        event = events[0]
        data_value = event.get("XXX")
        data_dict = icalio.get_ical_dict(event, "XXX")

        self.assertEqual(data_value, "5")
        self.assertEqual(data_dict, {"AAA": "1", "BBB": "2"})

    def test_io_task_empty(self):
        manager = Manager()
        self.assertEqual(len(manager.getTasksAll()), 0)
        newManager = execute_ical_io(manager)
        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 0)

    def test_io_task_basic(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        manager.addTask(task)
        self.assertEqual(len(manager.getTasksAll()), 1)

        task.title = "title example"
        task.description = "description example"
        task.completed = 66
        task.priority = 5
        startDateTime = datetime.datetime(year=2022, month=6, day=16, hour=12, minute=34)
        dueDateTime = datetime.datetime(year=2022, month=6, day=16, hour=13, minute=45)
        task.setOccurrence(startDateTime, dueDateTime)
        self.assertEqual(task.dueDateTime, task.dueDateTime)

        newManager = execute_ical_io(manager)

        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 1)
        newTask: LocalTask = newTasks[0]

        self.assertEqual(newTask.UID, task.UID)
        self.assertEqual(newTask.title, task.title)
        self.assertEqual(newTask.description, task.description)
        self.assertEqual(newTask.completed, task.completed)
        self.assertEqual(newTask.priority, task.priority)
        self.assertEqual(newTask.startDateTime.replace(tzinfo=None), task.startDateTime)
        self.assertEqual(newTask.dueDateTime.replace(tzinfo=None), task.dueDateTime)

    def test_io_task_dtstart_none(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        manager.addTask(task)
        self.assertEqual(len(manager.getTasksAll()), 1)

        task.title = "title example"
        dueDateTime = datetime.datetime(year=2022, month=6, day=16, hour=13, minute=45, tzinfo=datetime.timezone.utc)
        task.setOccurrenceDue(dueDateTime)

        newManager = execute_ical_io(manager)

        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 1)
        newTask: LocalTask = newTasks[0]

        self.assertEqual(newTask.title, task.title)
        self.assertEqual(newTask.startDateTime, task.startDateTime)
        self.assertEqual(newTask.dueDateTime, task.dueDateTime)

    def test_io_task_recurrence(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        manager.addTask(task)
        self.assertEqual(len(manager.getTasksAll()), 1)

        task.title = "title example"
        dueDateTime = datetime.datetime(year=2022, month=6, day=16, hour=13, minute=45, tzinfo=datetime.timezone.utc)
        task.setOccurrenceDue(dueDateTime)
        task.recurrence = Recurrent(RepeatType.DAILY, 3, datetime.date(year=2023, month=9, day=18))
        task.setCompleted()  ## progress recurrence

        newManager = execute_ical_io(manager)

        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 1)
        newTask: LocalTask = newTasks[0]

        self.assertEqual(newTask.UID, task.UID)
        self.assertEqual(newTask.title, task.title)
        self.assertEqual(newTask.dueDateTime, task.dueDateTime)
        self.assertEqual(newTask.recurrence, task.recurrence)
        self.assertEqual(newTask.dueDateTime, task.dueDateTime)

    def test_io_task_subitems(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        manager.addTask(task)
        task.title = "title example"
        subTask = task.addSubTask()
        subTask.title = "subtitle example"

        self.assertEqual(len(manager.getTasksAll()), 2)

        newManager = execute_ical_io(manager)

        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 2)

        newTask: LocalTask = newTasks[0]
        self.assertEqual(newTask.UID, task.UID)
        self.assertEqual(newTask.title, task.title)
        newSubTask: LocalTask = newTasks[1]
        self.assertEqual(newSubTask.UID, subTask.UID)
        self.assertEqual(newSubTask.title, subTask.title)
        self.assertEqual(newSubTask.getParent(), newTask)

    def test_io_task_reminder(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        manager.addTask(task)
        task.title = "title example"
        task.addReminderDays(2)

        self.assertEqual(len(manager.getTasksAll()), 1)

        newManager = execute_ical_io(manager)

        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 1)

        newTask: LocalTask = newTasks[0]
        self.assertEqual(newTask.UID, task.UID)
        self.assertEqual(newTask.title, task.title)
        self.assertEqual(len(newTask.reminderList), 1)
        self.assertEqual(str(newTask.reminderList[0]), str(Reminder(days=2)))

    def test_io_task_reminder_list(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        manager.addTask(task)
        task.title = "title example"
        task.addReminderDays(2)
        task.addReminderDays(5)

        self.assertEqual(len(manager.getTasksAll()), 1)

        newManager = execute_ical_io(manager)

        newTasks = newManager.getTasksAll()
        self.assertEqual(len(newTasks), 1)

        newTask: LocalTask = newTasks[0]
        self.assertEqual(newTask.UID, task.UID)
        self.assertEqual(newTask.title, task.title)
        self.assertEqual(len(newTask.reminderList), 2)
        self.assertEqual(str(newTask.reminderList[0]), str(Reminder(days=2)))
        self.assertEqual(str(newTask.reminderList[1]), str(Reminder(days=5)))

    def test_timedelta_from_string(self):
        time_delta = timedelta_from_string("1 day")
        self.assertTrue(time_delta is not None)
        self.assertEqual(time_delta, timedelta(days=1))

        time_delta = timedelta_from_string("3 days")
        self.assertTrue(time_delta is not None)
        self.assertEqual(time_delta, timedelta(days=3))

        time_delta = timedelta_from_string("333 days")
        self.assertTrue(time_delta is not None)
        self.assertEqual(time_delta, timedelta(days=333))

    def test_export_icalendar_task(self):
        manager = Manager()
        task: LocalTask = manager.createEmptyTask()
        task.UID = "1111-2222-3333-4444"
        task._createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # pylint: disable=W0212
        task._lastModifiedDate = datetime.datetime(2025, 11, 23, 9, 20, 30)  # pylint: disable=W0212
        manager.addTask(task)
        task.title = "title example"
        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = replace_line(content, "DTSTAMP:", "20251111T190206Z")
        self.assertEqual(
            """\
BEGIN:VCALENDAR
PRODID:-//Hanlendar//EN
BEGIN:VEVENT
SUMMARY:title example
DTSTAMP:20251111T190206Z
UID:1111-2222-3333-4444
CREATED:20251122T092030Z
LAST-MODIFIED:20251123T092030Z
END:VEVENT
END:VCALENDAR
""",
            content,
        )

    def test_export_icalendar_todo(self):
        manager = Manager()
        todo: LocalToDo = manager.createEmptyToDo()
        todo.UID = "1111-2222-3333-4444"
        todo._createDate = datetime.datetime(2025, 11, 22, 9, 20, 30)  # pylint: disable=W0212
        manager.addToDo(todo)
        todo.title = "title example"
        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = replace_line(content, "DTSTAMP:", "20251123T092030Z")
        content = replace_line(content, "LAST-MODIFIED:", "20251123T092130Z")
        self.assertEqual(
            """\
BEGIN:VCALENDAR
PRODID:-//Hanlendar//EN
BEGIN:VTODO
CREATED:20251122T092030Z
DTSTAMP:20251123T092030Z
LAST-MODIFIED:20251123T092130Z
SUMMARY:title example
UID:1111-2222-3333-4444
END:VTODO
END:VCALENDAR
""",
            content,
        )

    ## =======================================================================

    def test_evolution_all_day_event_basic(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_all_day_event_basic.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("49c4245a00131e320f35c0b1ba360d7d23b0a0af", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 11, 14, 3, 31), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 11, 15, 3, 31),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 28, 0, 0), new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 29, 0, 0), new_item.endDateTime)
        self.assertEqual("summary data", new_item.summary)
        self.assertEqual("location data", new_item.location)
        self.assertEqual("webpage data", new_item.url)
        self.assertEqual("description data", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual({"CLASS": b"PUBLIC", "COLOR": b"fuchsia", "TRANSP": b"OPAQUE"}, new_item.unknownProps)

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T211247Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_all_day_event_full(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_all_day_event_full.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("061269e77012385c9d603051e26a8a43a534e9a8", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 6, 22, 52, 59), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 6, 22, 52, 59),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 25, 0, 0), new_item.startDateTime)
        self.assertEqual(datetime.datetime(2025, 11, 26, 0, 0), new_item.dueDateTime)
        self.assertEqual("evolution all day event", new_item.summary)
        self.assertEqual("loc", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "CLASS": b"PUBLIC",
                "EXDATE": b"20251106",
                "RRULE": b"FREQ=DAILY;COUNT=2",
                "STATUS": b"TENTATIVE",
                "TRANSP": b"OPAQUE",
                "subcomponents": {
                    "VALARM": b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:ev"
                    b"olution all day event\r\nTRIGGER;RELATED=END:-"
                    b"PT15M\r\nX-EVOLUTION-ALARM-UID:234e78a29144053"
                    b"f40193800fb08a18722cb0f79\r\nEND:VALARM\r\n",
                },
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T211247Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(event_ical_content, "EXDATE;", "EXDATE:20251106", replace_whole_line=True)

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_appointment_full(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_appointment_full.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("a9029b2d-bb58-11f0-ad88-80fa5b58053f", new_item.UID)
        self.assertEqual(None, new_item.createDateTime)
        self.assertEqual(
            datetime.datetime(2025, 11, 6, 22, 48, 19),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 24, 10, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 11, 24, 11, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("evolution full example", new_item.summary)
        self.assertEqual("location", new_item.location)
        self.assertEqual("web", new_item.url)
        self.assertEqual("descr", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "ATTACH": b"https://google.pl",
                "CLASS": b"PUBLIC",
                "COLOR": b"yellow",
                "RRULE": b"FREQ=DAILY;COUNT=2;INTERVAL=3",
                "STATUS": b"CANCELLED",
                "TRANSP": b"OPAQUE",
                "subcomponents": {
                    "VALARM": b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:ev"
                    b"olution full example\r\nTRIGGER;RELATED=START:"
                    b"-PT15M\r\nX-EVOLUTION-ALARM-UID:98686f444ce13b"
                    b"e455218bfc72170a45a8c25e32\r\nEND:VALARM\r\n",
                },
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T213631Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "ATTACH;",
            "ATTACH:https://google.pl",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "RRULE;",
            "RRULE:FREQ=DAILY;COUNT=2;INTERVAL=3",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_task_basic(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_basic.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("7c72ab99414ca6dfe803be5765508d9055909706", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 8, 1, 2, 51), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 11, 8, 1, 2, 51), new_item.lastModifiedDateTime.replace(tzinfo=None))
        self.assertEqual("evolution task sample", new_item.summary)
        self.assertEqual("", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {"CLASS": b"CONFIDENTIAL", "DUE": b"20251122", "PERCENT-COMPLETE": b"45", "STATUS": b"IN-PROCESS"},
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251104T195837Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_evolution_task_completed(self):
        ## compatibility with evolution

        event_path = get_data_path("evolution_task_completed.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalToDo = new_items[0]
        self.assertEqual(LocalToDo, type(new_item))
        self.assertEqual("f5dccad88abe34db1e29b7432b1c2dd9d1169316", new_item.UID)
        self.assertEqual(datetime.datetime(2025, 11, 13, 21, 34, 59), new_item.createDateTime.replace(tzinfo=None))
        self.assertEqual(
            datetime.datetime(2025, 11, 13, 21, 35, 38),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual("evolution todo start end", new_item.summary)
        self.assertEqual("todo location", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("todo descr", new_item.description)
        self.assertEqual(2, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "CLASS": b"PUBLIC",
                "COMPLETED": b"20251113T000000Z",
                "DTSTART": b"20251114",
                "DUE": b"20251116",
                "ESTIMATED-DURATION": b"P1DT2H3M",
                "PERCENT-COMPLETE": b"100",
                "STATUS": b"COMPLETED",
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251108T000146Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_onecalendar_item_all_day(self):
        ## compatibility with evolution

        event_path = get_data_path("onecalendar_item_all_day.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        self.assertDictEqual({}, manager.unknownProps)

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("be4f8f17-1cd6-4432-9686-c113391b6058", new_item.UID)
        self.assertEqual(None, new_item.createDateTime)
        self.assertEqual(
            datetime.datetime(2025, 11, 6, 23, 12, 3),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 11, 20, 0, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 11, 21, 0, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("🌴 Onecal all day item", new_item.summary)
        self.assertEqual("Loc", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("desc", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "RRULE": b"FREQ=WEEKLY;UNTIL=20251130;INTERVAL=1;BYDAY=WE,SA",
                "X-ONECAL-CATEGORYID": b"107",
                "subcomponents": {
                    "VALARM": b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:Re"
                    b"minder\r\nTRIGGER:-PT12H\r\nEND:VALARM\r\n",
                },
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251106T221203Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        event_ical_content = remove_line(event_ical_content, "CALSCALE:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "ATTACH;",
            "ATTACH:https://google.pl",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "RRULE;",
            "RRULE:FREQ=DAILY;COUNT=2;INTERVAL=3",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )

    def test_onecalendar_item_reminder(self):
        ## compatibility with evolution

        event_path = get_data_path("onecalendar_item_reminder.ics")
        event_ical_content = read_file(event_path)

        manager = Manager()
        new_items, dangling_items = import_icalendar_content(manager, event_ical_content)

        self.assertEqual(1, len(new_items))
        self.assertEqual(0, len(dangling_items))

        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "subcomponents": {
                    "VTIMEZONE": b"BEGIN:VTIMEZONE\r\nTZID:Europe/Warsaw\r\nBEGIN:STANDARD\r\nDTS"
                    b"TART:20001029T030000\r\nRRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=1"
                    b"0\r\nTZNAME:CET\r\nTZOFFSETFROM:+0200\r\nTZOFFSETTO:+0100\r"
                    b"\nEND:STANDARD\r\nBEGIN:DAYLIGHT\r\nDTSTART:20000326T020000\r\n"
                    b"RRULE:FREQ=YEARLY;BYDAY=-1SU;BYMONTH=3\r\nTZNAME:CEST\r\nTZO"
                    b"FFSETFROM:+0100\r\nTZOFFSETTO:+0200\r\nEND:DAYLIGHT\r\nEND:VTI"
                    b"MEZONE\r\n",
                },
            },
            manager.unknownProps,
        )

        new_item: LocalTask = new_items[0]
        self.assertEqual(LocalTask, type(new_item))
        self.assertEqual("b6909c08-af3a-4686-82de-07126cc6f9ba", new_item.UID)
        self.assertEqual(None, new_item.createDateTime)
        self.assertEqual(
            datetime.datetime(2025, 11, 11, 22, 45, 27),
            new_item.lastModifiedDateTime.replace(tzinfo=None),
        )
        self.assertEqual(datetime.datetime(2025, 12, 18, 12, 0), new_item.startDateTime.replace(tzinfo=None))
        self.assertEqual(datetime.datetime(2025, 12, 18, 13, 0), new_item.dueDateTime.replace(tzinfo=None))
        self.assertEqual("Xxx onecal", new_item.summary)
        self.assertEqual("Loc data", new_item.location)
        self.assertEqual("", new_item.url)
        self.assertEqual("desc data with reminder 45mins", new_item.description)
        self.assertEqual(1, new_item.sequence)
        # TODO: all unknown props should be handled
        self.assertDictEqual(
            {
                "X-ONECAL-CATEGORYID": b"110",
                "subcomponents": {
                    "VALARM": b"BEGIN:VALARM\r\nACTION:DISPLAY\r\nDESCRIPTION:Re"
                    b"minder\r\nTRIGGER:-PT45M\r\nEND:VALARM\r\n",
                },
            },
            new_item.unknownProps,
        )

        content = export_icalendar_content(manager)
        content = content.replace("\r\n", "\n")
        content = sort_ical_content(content)
        content = replace_line(content, "DTSTAMP:", "20251111T214527Z")

        event_ical_content = sort_ical_content(event_ical_content)
        event_ical_content = replace_line(event_ical_content, "PRODID:", "-//Hanlendar//EN")
        event_ical_content = remove_line(event_ical_content, "VERSION:")
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTEND;",
            "DTEND:20251218T120000Z",
            replace_whole_line=True,
        )
        # TODO: fix compatibility
        event_ical_content = replace_line(
            event_ical_content,
            "DTSTART;",
            "DTSTART:20251218T110000Z",
            replace_whole_line=True,
        )

        self.assertEqual(
            event_ical_content,
            content,
        )


##
def execute_ical_io(manager: Manager):
    content = export_icalendar_content(manager)
    new_manager = Manager()
    import_icalendar_content(new_manager, content)
    return new_manager
