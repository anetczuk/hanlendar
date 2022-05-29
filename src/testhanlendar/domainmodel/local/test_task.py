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

from hanlendar.domainmodel.local.task import Task
from hanlendar.domainmodel.local.reminder import Reminder
from hanlendar.domainmodel.local.recurrent import Recurrent


class TaskTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_setCompleted(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.setDefaultDate( taskDate )

        task.setCompleted()
        self.assertEqual( task.completed, 100 )

    def test_setCompleted_recurrent(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.recurrence = Recurrent()
        task.recurrence.setDaily()
        task.setDefaultDate( taskDate )

        task.setCompleted()
        self.assertEqual( task.completed, 0 )
        self.assertEqual( task.occurrenceStart.date(), datetime.date( 2020, 5, 18 ) )
        self.assertEqual( task.occurrenceDue.date(), datetime.date( 2020, 5, 18 ) )

    def test_getTaskOccurrenceForDate(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDateTime = taskDate

        entry = task.getTaskOccurrenceForDate( taskDate.date() )
        self.assertEqual( entry.task, task )
        self.assertEqual( entry.offset, 0 )

    def test_getTaskOccurrenceForDate_recurrent(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDateTime = taskDate
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        entry = task.getTaskOccurrenceForDate( taskDate.date() + timedelta( days=2 ) )
        self.assertEqual( entry.task, task )
        self.assertEqual( entry.offset, 2 )

    def test_getTaskOccurrenceForDate_recurrent_far(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDateTime = taskDate
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        entry = task.getTaskOccurrenceForDate( taskDate.date() + timedelta( days=3333 * 366 ) )
        self.assertEqual( entry.task, task )
        self.assertEqual( entry.offset, 1219878 )

    def test_getTaskOccurrenceForDate_recurrent_endDate(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDateTime = taskDate
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)
        task.recurrence.endDate = taskDate.date() + timedelta( days=5 )

        entry = task.getTaskOccurrenceForDate( taskDate.date() + timedelta( days=9 ) )
        self.assertEqual( entry, None )

    def test_getTaskOccurrenceForDate_recurrent_completed(self):
        task = Task()
        todayDate = datetime.datetime.today()
        dueDate = todayDate.replace( day=8, hour=12 )
        task.dueDateTime = dueDate
        task.recurrence = Recurrent()
        task.recurrence.setWeekly()
        task.setCompleted()                ## mark first occurrence completed

        occurrence1 = task.getTaskOccurrenceForDate( dueDate.date() - timedelta( days=7 ) )
        self.assertEqual( occurrence1, None )

        occurrence2 = task.getTaskOccurrenceForDate( dueDate.date() )
        self.assertNotEqual( occurrence2, None )
        self.assertEqual( occurrence2.isCompleted(), True )

        occurrence3 = task.getTaskOccurrenceForDate( dueDate.date() + timedelta( days=7 ) )
        self.assertNotEqual( occurrence3, None )
        self.assertEqual( occurrence3.isCompleted(), False )

    def test_getNotifications_due(self):
        task = Task()
        task.title = "task 1"
        task.dueDateTime = datetime.datetime.today() + datetime.timedelta( seconds=10 )

        notifications = task.getNotifications()
        self.assertEqual( len(notifications), 1 )
        self.assertEqual( notifications[0].task, task )
        self.assertEqual( notifications[0].message, "task 'task 1' reached deadline" )

    def test_getNotifications_reminder(self):
        task = Task()
        task.title = "task 1"
        task.dueDateTime = datetime.datetime.today() + datetime.timedelta( seconds=30 )

        reminder = Reminder()
        reminder.setTime( 0, 10 )
        task.addReminder( reminder )

        notifications = task.getNotifications()
        self.assertEqual( len(notifications), 2 )
        self.assertEqual( notifications[0].task, task )
        self.assertEqual( notifications[0].message, "task 'task 1': 0:00:10 before due time" )
        self.assertEqual( notifications[1].task, task )
        self.assertEqual( notifications[1].message, "task 'task 1' reached deadline" )


class TaskOccurrenceTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_date_current_subtask(self):
        task = Task()
        task.startDateTime = datetime.datetime( 2020, 10, 10 )
        task.dueDateTime   = task.startDateTime + timedelta( days=1 )

        subtask = task.addSubTask()
        subtask.setDeadline()
#         subtask.startDateTime = task.startDateTime - timedelta( days=5 )
        subtask.dueDateTime   = task.dueDateTime   - timedelta( days=7 )

        occurrence = task.currentOccurrence()
        self.assertEqual( occurrence.startCurrent, task.startDateTime )
        self.assertEqual( occurrence.dueCurrent, subtask.dueDateTime )

    def test_isTimedout(self):
        task = Task()
        occurrence = task.currentOccurrence()
        self.assertEqual( occurrence.isTimedout(), False )

    def test_isReminded(self):
        task = Task()
        task.dueDateTime = datetime.datetime.today() + datetime.timedelta( seconds=30 )

        occurrence = task.currentOccurrence()
        self.assertEqual( occurrence.isReminded(), False )

    def test_isReminded_reminded(self):
        task = Task()
        task.dueDateTime = datetime.datetime.today() + datetime.timedelta( seconds=30 )

        reminder = Reminder()
        reminder.setTime( 0, 300 )
        task.addReminder( reminder )

        occurrence = task.currentOccurrence()
        self.assertEqual( occurrence.isReminded(), True )
