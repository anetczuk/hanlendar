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

import hanlendar.domainmodel.icalio as icalio
from hanlendar.domainmodel.icalio import import_icalendar_content, \
    export_icalendar_content, fix_dangling_tasks

from hanlendar.domainmodel.recurrent import Recurrent, RepeatType
from hanlendar.domainmodel.local.manager import LocalManager as Manager
from hanlendar.domainmodel.local.task import LocalTask as Task
from hanlendar.domainmodel.reminder import Reminder


class ICalIOTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

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
        self.assertEqual( len(tasks), 0 )

        import_icalendar_content( manager, content )

        tasks = manager.getTasksAll()
        self.assertEqual( len(tasks), 1 )

        calTask = tasks[0]
        self.assertEqual( calTask.UID, "1234__4321" )
        self.assertEqual( calTask.title, "Umówiona wizyta, Remiza Warszawska 123" )
        self.assertEqual( calTask.startDateTime, datetime.datetime(2022, 4, 14, 15, 20) )
        self.assertEqual( calTask.dueDateTime, datetime.datetime(2022, 4, 14, 15, 40) )

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
        self.assertEqual( len(tasks), 0 )

        import_icalendar_content( manager, content )

        tasks = manager.getTasksAll()
        self.assertEqual( len(tasks), 1 )

        calTask = tasks[0]
        self.assertEqual( calTask.UID, "1234__4321" )
        self.assertEqual( calTask.title, "Umówiona wizyta, Remiza Warszawska 123" )
        self.assertEqual( calTask.startDateTime, datetime.datetime(2022, 4, 14, 15, 20) )
        self.assertEqual( calTask.dueDateTime, datetime.datetime(2022, 4, 14, 15, 40) )

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
        self.assertEqual( len(tasks), 0 )

        import_icalendar_content( manager, content )

        tasks = manager.getTasksAll()
        self.assertEqual( len(tasks), 1 )

        calTask = tasks[0]
        self.assertEqual( calTask.UID, "1234__4321" )
        self.assertEqual( calTask.title, "Umówiona wizyta, Remiza Warszawska 123" )
        self.assertEqual( calTask.startDateTime, datetime.datetime(2022, 4, 14, 15, 20) )
        self.assertEqual( calTask.dueDateTime, datetime.datetime(2022, 4, 14, 15, 40) )
        self.assertEqual( calTask.completed, 100 )

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
        self.assertEqual( len(tasks), 0 )

        _, dangling_children = import_icalendar_content( manager, content )
        fix_dangling_tasks( manager, dangling_children )

        newTasks = manager.getTasksAll()
        self.assertEqual( len(newTasks), 2 )

        newTask: Task = newTasks[0]
        self.assertEqual( newTask.UID, "284cd1d8-701a-4bea-8603-3cf4dd9a1260@hanlendar" )
        self.assertEqual( newTask.title, "title example" )
        newSubTask: Task = newTasks[1]
        self.assertEqual( newSubTask.UID, "1212afc7-09c2-4ee5-88f6-2829e247e9d6@hanlendar" )
        self.assertEqual( newSubTask.title, "a subtitle example" )
        self.assertEqual( newSubTask.getParent(), newTask )

    def test_io_list(self):
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
        ievent = icalendar.cal.Event()
        event_data_list = [ 1, 2, 4, 3 ]
        icalio.set_ical_list( ievent, 'XXX', event_data_list )
        calendar.add_component( ievent )
        calendar_string = calendar.to_ical()
        calendar_string = calendar_string.decode("utf-8")

        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar.from_ical( calendar_string )
        events = calendar.walk( "VEVENT" )
        event = events[0]
        data_list = icalio.get_ical_list( event, 'XXX' )

        self.assertEqual( data_list, [ '1', '2', '4', '3' ] )

    def test_io_list_comma(self):
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
        ievent = icalendar.cal.Event()
        event_data_list = [ '1,11', '2,22', '3,33', '4,44' ]
        icalio.set_ical_list( ievent, 'XXX', event_data_list )
        calendar.add_component( ievent )
        calendar_string = calendar.to_ical()
        calendar_string = calendar_string.decode("utf-8")

        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar.from_ical( calendar_string )
        events = calendar.walk( "VEVENT" )
        event = events[0]
        data_list = icalio.get_ical_list( event, 'XXX' )

        self.assertEqual( data_list, event_data_list )

    def test_io_dict(self):
        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar()
        ievent = icalendar.cal.Event()
        event_data_dict = {'aaa': '1', 'bbb': '2' }
        icalio.set_ical_dict( ievent, 'XXX', 5, event_data_dict )
        calendar.add_component( ievent )
        calendar_string = calendar.to_ical()
        calendar_string = calendar_string.decode("utf-8")

        calendar: icalendar.cal.Calendar = icalendar.cal.Calendar.from_ical( calendar_string )
        events = calendar.walk( "VEVENT" )
        event = events[0]
        data_value = icalio.get_ical_value( event, 'XXX' )
        data_dict  = icalio.get_ical_dict( event, 'XXX' )

        self.assertEqual( data_value, '5' )
        self.assertEqual( data_dict, {'AAA': '1', 'BBB': '2' } )

    def test_io_task_empty(self):
        manager = Manager()
        self.assertEqual( len( manager.getTasksAll() ), 0 )
        newManager = execute_io( manager )
        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 0 )

    def test_io_task_basic(self):
        manager = Manager()
        task: Task = manager.createEmptyTask()
        manager.addTask( task )
        self.assertEqual( len( manager.getTasksAll() ), 1 )

        task.title         = "title example"
        task.description   = "description example"
        task.completed     = 66
        task.priority      = 5
        task.startDateTime = datetime.datetime( year=2022, month=6, day=16, hour=12, minute=34 )
        task.dueDateTime   = datetime.datetime( year=2022, month=6, day=16, hour=13, minute=45 )
        self.assertEqual( task.occurrenceDue, task.dueDateTime )

        newManager = execute_io( manager )

        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 1 )
        newTask: Task = newTasks[0]

        self.assertEqual( newTask.UID, task.UID )
        self.assertEqual( newTask.title, task.title )
        self.assertEqual( newTask.description, task.description )
        self.assertEqual( newTask.completed, task.completed )
        self.assertEqual( newTask.priority, task.priority )
        self.assertEqual( newTask.startDateTime, task.startDateTime )
        self.assertEqual( newTask.dueDateTime, task.dueDateTime )
        self.assertEqual( newTask.occurrenceDue, task.occurrenceDue )

    def test_io_task_dtstart_none(self):
        manager = Manager()
        task: Task = manager.createEmptyTask()
        manager.addTask( task )
        self.assertEqual( len( manager.getTasksAll() ), 1 )

        task.title         = "title example"
        task.startDateTime = None
        task.dueDateTime   = datetime.datetime( year=2022, month=6, day=16, hour=13, minute=45 )

        newManager = execute_io( manager )

        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 1 )
        newTask: Task = newTasks[0]

        self.assertEqual( newTask.title, task.title )
        self.assertEqual( newTask.startDateTime, task.startDateTime )
        self.assertEqual( newTask.dueDateTime, task.dueDateTime )

    def test_io_task_reccurence(self):
        manager = Manager()
        task: Task = manager.createEmptyTask()
        manager.addTask( task )
        self.assertEqual( len( manager.getTasksAll() ), 1 )

        task.title           = "title example"
        task.dueDateTime     = datetime.datetime( year=2022, month=6, day=16, hour=13, minute=45 )
        task.recurrence      = Recurrent( RepeatType.DAILY, 3, datetime.date( year=2023, month=9, day=18 ) )
        task.recurrentOffset = 6

        newManager = execute_io( manager )

        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 1 )
        newTask: Task = newTasks[0]

        self.assertEqual( newTask.UID, task.UID )
        self.assertEqual( newTask.title, task.title )
        self.assertEqual( newTask.dueDateTime, task.dueDateTime )
        self.assertEqual( newTask.recurrentOffset, task.recurrentOffset )
        self.assertEqual( newTask.recurrence, task.recurrence )
        self.assertEqual( newTask.occurrenceDue, task.occurrenceDue )

    def test_io_task_subitems(self):
        manager = Manager()
        task: Task = manager.createEmptyTask()
        manager.addTask( task )
        task.title = "title example"
        subTask = task.addSubTask()
        subTask.title = "subtitle example"

        self.assertEqual( len( manager.getTasksAll() ), 2 )

        newManager = execute_io( manager )

        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 2 )

        newTask: Task = newTasks[0]
        self.assertEqual( newTask.UID, task.UID )
        self.assertEqual( newTask.title, task.title )
        newSubTask: Task = newTasks[1]
        self.assertEqual( newSubTask.UID, subTask.UID )
        self.assertEqual( newSubTask.title, subTask.title )
        self.assertEqual( newSubTask.getParent(), newTask )

    def test_io_task_reminder(self):
        manager = Manager()
        task: Task = manager.createEmptyTask()
        manager.addTask( task )
        task.title = "title example"
        task.addReminderDays( 2 )

        self.assertEqual( len( manager.getTasksAll() ), 1 )

        newManager = execute_io( manager )

        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 1 )

        newTask: Task = newTasks[0]
        self.assertEqual( newTask.UID, task.UID )
        self.assertEqual( newTask.title, task.title )
        self.assertEqual( len(newTask.reminderList), 1 )
        self.assertEqual( str( newTask.reminderList[0] ), str( Reminder(days=2) ) )

    def test_io_task_reminder_list(self):
        manager = Manager()
        task: Task = manager.createEmptyTask()
        manager.addTask( task )
        task.title = "title example"
        task.addReminderDays( 2 )
        task.addReminderDays( 5 )

        self.assertEqual( len( manager.getTasksAll() ), 1 )

        newManager = execute_io( manager )

        newTasks = newManager.getTasksAll()
        self.assertEqual( len( newTasks ), 1 )

        newTask: Task = newTasks[0]
        self.assertEqual( newTask.UID, task.UID )
        self.assertEqual( newTask.title, task.title )
        self.assertEqual( len(newTask.reminderList), 2 )
        self.assertEqual( str( newTask.reminderList[0] ), str( Reminder(days=2) ) )
        self.assertEqual( str( newTask.reminderList[1] ), str( Reminder(days=5) ) )


##
def execute_io( manager: Manager ):
    content = export_icalendar_content( manager )
    new_manager = Manager()
    import_icalendar_content( new_manager, content )
    return new_manager
