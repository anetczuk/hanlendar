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

from todocalendar.domainmodel.task import Task
from todocalendar.domainmodel.reminder import Reminder
from todocalendar.domainmodel.recurrent import Recurrent


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
        self.assertEqual( task.startDate.date(), datetime.date( 2020, 5, 18 ) )
        self.assertEqual( task.dueDate.date(), datetime.date( 2020, 5, 18 ) )

    def test_hasEntryExact_None(self):
        task = Task()
        task.title = "xxx"
        taskDate = datetime.date( 2020, 5, 17 )
        self.assertEqual( task.hasEntryExact(taskDate), False )

    def test_hasEntryExact_entries(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.title = "xxx"
        task.setDefaultDate( taskDate )
        self.assertEqual( task.hasEntryExact(taskDate), True )

    def test_hasEntryExact_recurrent(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.title = "xxx"
        task.setDefaultDate( taskDate )
        task.recurrence = Recurrent()
        task.recurrence.setDaily()

        recurrentDate = taskDate + timedelta(days=5)
        self.assertEqual( task.hasEntryExact(recurrentDate), True )

    def test_hasEntryExact_recurrent_far(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.title = "xxx"
        task.setDefaultDate( taskDate )
        task.recurrence = Recurrent()
        task.recurrence.setDaily()

        recurrentDate = taskDate + timedelta( days=3333 * 366 )
        self.assertEqual( task.hasEntryExact(recurrentDate), True )

    def test_hasEntryExact_recurrent_endDate(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.title = "xxx"
        task.setDefaultDate( taskDate )
        task.recurrence = Recurrent()
        task.recurrence.setDaily()
        task.recurrence.endDate = taskDate + timedelta(days=3)

        recurrentDate = taskDate + timedelta(days=5)
        self.assertEqual( task.hasEntryExact(recurrentDate), False )

    def test_hasEntryInMonth(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.setDefaultDate( taskDate )
        has = task.hasEntryInMonth( taskDate )

        self.assertEqual( has, True )

    def test_hasEntryInMonth_recurrent_far(self):
        taskDate = datetime.date( 2020, 5, 17 )
        task = Task()
        task.setDefaultDate( taskDate )
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        entryDate = taskDate + timedelta( days=3333 * 366 )
        has = task.hasEntryInMonth( entryDate )

        self.assertEqual( has, True )

    def test_getEntryForDate(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDate = taskDate

        entry = task.getEntryForDate( taskDate.date() )
        self.assertEqual( entry.task, task )
        self.assertEqual( entry.offset, 0 )

    def test_getEntryForDate_recurrent(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDate = taskDate
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        entry = task.getEntryForDate( taskDate.date() + timedelta( days=2 ) )
        self.assertEqual( entry.task, task )
        self.assertEqual( entry.offset, 2 )

    def test_getEntryForDate_recurrent_far(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDate = taskDate
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        entry = task.getEntryForDate( taskDate.date() + timedelta( days=3333 * 366 ) )
        self.assertEqual( entry.task, task )
        self.assertEqual( entry.offset, 1219878 )

    def test_getEntryForDate_recurrent_endDate(self):
        taskDate = datetime.datetime( 2020, 5, 17 )
        task = Task()
        task.dueDate = taskDate
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)
        task.recurrence.endDate = taskDate.date() + timedelta( days=5 )

        entry = task.getEntryForDate( taskDate.date() + timedelta( days=9 ) )
        self.assertEqual( entry, None )

    def test_getNotifications_due(self):
        task = Task()
        task.title = "task 1"
        task.dueDate = datetime.datetime.today() + datetime.timedelta( seconds=10 )

        notifications = task.getNotifications()
        self.assertEqual( len(notifications), 1 )
        self.assertEqual( notifications[0].task, task )
        self.assertEqual( notifications[0].message, "task 'task 1' reached deadline" )

    def test_getNotifications_reminder(self):
        task = Task()
        task.title = "task 1"
        task.dueDate = datetime.datetime.today() + datetime.timedelta( seconds=30 )

        reminder = Reminder()
        reminder.setTime( 0, 10 )
        task.addReminder( reminder )

        notifications = task.getNotifications()
        self.assertEqual( len(notifications), 2 )
        self.assertEqual( notifications[0].task, task )
        self.assertEqual( notifications[0].message, "task 'task 1': 0:00:10 before due time" )
        self.assertEqual( notifications[1].task, task )
        self.assertEqual( notifications[1].message, "task 'task 1' reached deadline" )

    def test_isTimedout(self):
        task = Task()
        self.assertEqual( task.isTimedout(), False )

    def test_isReminded(self):
        task = Task()
        task.dueDate = datetime.datetime.today() + datetime.timedelta( seconds=30 )
        self.assertEqual( task.isReminded(), False )

    def test_isReminded_reminded(self):
        task = Task()
        task.dueDate = datetime.datetime.today() + datetime.timedelta( seconds=30 )

        reminder = Reminder()
        reminder.setTime( 0, 300 )
        task.addReminder( reminder )

        self.assertEqual( task.isReminded(), True )
