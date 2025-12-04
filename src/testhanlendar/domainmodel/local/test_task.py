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
import copy

from hanlendar.domainmodel.reminder import Reminder
from hanlendar.domainmodel.recurrent import Recurrent, RepeatType
from hanlendar.domainmodel.local.task import LocalTask
from hanlendar.domainmodel.taskoccurrence import TaskOccurrence, DateTimeRange


class TaskTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_compare_self(self):
        item = LocalTask()

        # ruff: noqa: PLR0124
        self.assertTrue(item == item)  # pylint: disable=R0124
        # ruff: noqa: PLR0124
        self.assertTrue(item is item)  # pylint: disable=R0124
        # ruff: noqa: PLR0124
        self.assertFalse(item != item)  # pylint: disable=R0124
        self.assertEqual(item, item)

    def test_compare_copy(self):
        item_01 = LocalTask()
        item_02 = copy.deepcopy(item_01)

        self.assertTrue(item_01 == item_02)
        self.assertFalse(item_01 is item_02)
        self.assertFalse(item_01 != item_02)
        self.assertEqual(item_01, item_02)

    def test_compare_equal(self):
        item_01 = LocalTask()
        item_02 = LocalTask()
        item_02.commonData.UID = item_01.commonData.UID
        item_02.commonData.createDate = item_01.commonData.createDate
        item_02.commonData.lastModifiedDate = item_01.commonData.lastModifiedDate

        self.assertTrue(item_01 == item_02)
        self.assertFalse(item_01 is item_02)
        self.assertFalse(item_01 != item_02)
        self.assertEqual(item_01, item_02)

    def test_compare_diff(self):
        item_01 = LocalTask()
        item_02 = LocalTask()
        item_02.title = item_01.title + "xxx"

        self.assertFalse(item_01 == item_02)
        self.assertFalse(item_01 is item_02)
        self.assertTrue(item_01 != item_02)
        self.assertNotEqual(item_01, item_02)

    def test_in_self(self):
        item = LocalTask()
        item_set = {item}

        self.assertTrue(item in item_set)
        self.assertFalse(item not in item_set)
        self.assertIn(item, item_set)

    def test_in_copy(self):
        item_01 = LocalTask()
        item_set = {item_01}
        item_02 = copy.deepcopy(item_01)

        self.assertTrue(item_02 in item_set)
        self.assertFalse(item_02 not in item_set)
        self.assertIn(item_02, item_set)

    def test_in_diff_01(self):
        item_01 = LocalTask()
        item_set = {item_01}
        item_02 = LocalTask()
        item_02.title = f"{item_01.title}_xxx"

        self.assertFalse(item_02 in item_set)
        self.assertTrue(item_02 not in item_set)
        self.assertNotIn(item_02, item_set)

    def test_setCompleted(self):
        taskDate = datetime.date(2020, 5, 17)
        task = LocalTask()
        task.setDefaultDate(taskDate)

        self.assertEqual(task.startDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 17))

        task.setCompleted()

        self.assertEqual(task.completed, 100)
        self.assertTrue(task.isCompleted())
        self.assertEqual(task.startDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 17))

    def test_setCompleted_recurrent(self):
        taskDate = datetime.date(2020, 5, 17)
        task = LocalTask()
        task.recurrence = Recurrent()
        task.recurrence.setDaily()
        task.setDefaultDate(taskDate)

        self.assertEqual(task.startDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 17))

        task.setCompleted()

        self.assertEqual(task.completed, 0)
        self.assertEqual(task.startDate, datetime.date(2020, 5, 18))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 18))

    def test_setCompleted_recurrent_change(self):
        taskDate = datetime.date(2020, 5, 3)
        task = LocalTask()
        task.recurrence = Recurrent()
        task.recurrence.setWeekly()
        task.setDefaultDate(taskDate)

        task.setCompleted(50)
        self.assertEqual(task.completed, 50)
        self.assertEqual(task.startDate, datetime.date(2020, 5, 3))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 3))
        self.assertEqual(task.printNextRecurrence(), "2020-05-10 10:00")

        ## yes, complete twice
        task.setCompleted()
        task.setCompleted()

        self.assertEqual(task.completed, 0)
        # self.assertEqual(task.startDate, datetime.date(2020, 5, 17))
        # self.assertEqual(task.dueDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.startDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.printNextRecurrence(), "2020-05-24 10:00")

        ## change recurrence
        task.recurrence.setDaily()

        self.assertEqual(task.startDate, datetime.date(2020, 5, 17))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 17))

        task.setCompleted()

        self.assertEqual(task.startDate, datetime.date(2020, 5, 18))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 18))
        self.assertEqual(task.printNextRecurrence(), "2020-05-19 10:00")

    def test_setCompleted_history_001(self):
        taskDate = datetime.date(2020, 5, 2)
        task = LocalTask()
        task.recurrence = Recurrent()
        task.recurrence.setDaily()
        task.setDefaultDate(taskDate)

        task.setCompleted()
        task.setCompleted()

        self.assertListEqual(
            task.completedList,
            [
                DateTimeRange(datetime.datetime(2020, 5, 2, 10), datetime.datetime(2020, 5, 2, 11)),
                DateTimeRange(datetime.datetime(2020, 5, 3, 10), datetime.datetime(2020, 5, 3, 11)),
            ],
        )
        self.assertEqual(task.startDate, datetime.date(2020, 5, 4))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 4))

    def test_setCompleted_history_002(self):
        taskDate = datetime.date(2020, 5, 2)
        task = LocalTask()
        task.recurrence = Recurrent()
        task.setDefaultDate(taskDate)

        task.recurrence.setDaily()
        task.setCompleted()
        task.setCompleted()

        self.assertEqual(task.startDate, datetime.date(2020, 5, 4))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 4))

        task.recurrence.setWeekly()
        self.assertEqual(task.startDate, datetime.date(2020, 5, 4))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 4))

        task.setCompleted()

        self.assertEqual(task.startDate, datetime.date(2020, 5, 11))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 11))

        task.setCompleted()

        self.assertListEqual(
            task.completedList,
            [
                DateTimeRange(datetime.datetime(2020, 5, 2, 10), datetime.datetime(2020, 5, 2, 11)),
                DateTimeRange(datetime.datetime(2020, 5, 3, 10), datetime.datetime(2020, 5, 3, 11)),
                DateTimeRange(datetime.datetime(2020, 5, 4, 10), datetime.datetime(2020, 5, 4, 11)),
                DateTimeRange(datetime.datetime(2020, 5, 11, 10), datetime.datetime(2020, 5, 11, 11)),
            ],
        )

        self.assertEqual(task.startDate, datetime.date(2020, 5, 18))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 18))

    def test_deserialize_complete_list_v6(self):
        ## test deserialization of LocalTask version 6 and restore of "_completedList"

        task = LocalTask()
        obj_dict = {
            "_title": "task title",
            "_description": "task description",
            "_priority": 3,
            "_startDate": datetime.datetime(2020, 5, 2, 10),
            "_dueDate": datetime.datetime(2020, 5, 2, 11),
            "_completed": 0,
            "_recurrence": Recurrent(RepeatType.DAILY, 1),
            "_recurrentOffset": 3,
        }
        task.__dict__ = task._convertstate_(obj_dict, 3)  # pylint: disable=W0212

        self.assertListEqual(
            task.completedList,
            [
                DateTimeRange(datetime.datetime(2020, 5, 2, 10), datetime.datetime(2020, 5, 2, 11)),
                DateTimeRange(datetime.datetime(2020, 5, 3, 10), datetime.datetime(2020, 5, 3, 11)),
                DateTimeRange(datetime.datetime(2020, 5, 4, 10), datetime.datetime(2020, 5, 4, 11)),
            ],
        )
        self.assertEqual(task.startDate, datetime.date(2020, 5, 5))
        self.assertEqual(task.dueDate, datetime.date(2020, 5, 5))
        self.assertNotIn("_recurrentOffset", dir(task))

    def test_getTaskOccurrenceForDate(self):
        taskDate = datetime.datetime(2020, 5, 17)
        task = LocalTask()
        task.setOccurrenceDue(taskDate)

        entry: TaskOccurrence = task.getTaskOccurrenceForDate(taskDate.date())
        self.assertEqual(entry.task, task)

    def test_getTaskOccurrenceForDate_recurrent(self):
        taskDate = datetime.datetime(2020, 5, 17)
        task = LocalTask()
        task.setOccurrenceDue(taskDate)
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        find_date = taskDate.date() + timedelta(days=2)
        entry: TaskOccurrence = task.getTaskOccurrenceForDate(find_date)
        self.assertEqual(entry.task, task)

    def test_getTaskOccurrenceForDate_recurrent_far(self):
        taskDate = datetime.datetime(2020, 5, 17)
        task = LocalTask()
        task.setOccurrenceDue(taskDate)
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)

        entry: TaskOccurrence = task.getTaskOccurrenceForDate(taskDate.date() + timedelta(days=3333 * 366))
        self.assertEqual(entry.task, task)

    def test_getTaskOccurrenceForDate_recurrent_endDate(self):
        taskDate = datetime.datetime(2020, 5, 17)
        task = LocalTask()
        task.setOccurrenceDue(taskDate)
        task.recurrence = Recurrent()
        task.recurrence.setDaily(1)
        task.recurrence.endDate = taskDate.date() + timedelta(days=5)

        entry: TaskOccurrence = task.getTaskOccurrenceForDate(taskDate.date() + timedelta(days=9))
        self.assertEqual(entry, None)

    def test_getTaskOccurrenceForDate_recurrent_completed(self):
        task = LocalTask()
        todayDate = datetime.datetime.today()
        dueDate = todayDate.replace(day=8, hour=12)
        task.setOccurrenceDue(dueDate)
        task.recurrence = Recurrent()
        task.recurrence.setWeekly()
        task.setCompleted()  ## mark first occurrence completed

        occurrence1 = task.getTaskOccurrenceForDate(dueDate.date() - timedelta(days=7))
        self.assertEqual(occurrence1, None)

        occurrence2 = task.getTaskOccurrenceForDate(dueDate.date())
        self.assertNotEqual(occurrence2, None)
        self.assertEqual(occurrence2.isCompleted(), True)

        occurrence3 = task.getTaskOccurrenceForDate(dueDate.date() + timedelta(days=7))
        self.assertNotEqual(occurrence3, None)
        self.assertEqual(occurrence3.isCompleted(), False)

    def test_getNotifications_due(self):
        task = LocalTask()
        task.title = "task 1"
        dueDate = datetime.datetime.today() + datetime.timedelta(seconds=10)
        task.setOccurrenceDue(dueDate)

        notifications = task.getNotifications()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].task, task)
        self.assertEqual(notifications[0].message, "task 'task 1' reached deadline")

    def test_getNotifications_reminder(self):
        task = LocalTask()
        task.title = "task 1"
        dueDate = datetime.datetime.today() + datetime.timedelta(seconds=30)
        task.setOccurrenceDue(dueDate)

        reminder = Reminder()
        reminder.setTime(0, 10)
        task.addReminder(reminder)

        notifications = task.getNotifications()
        self.assertEqual(len(notifications), 2)
        self.assertEqual(notifications[0].task, task)
        self.assertEqual(notifications[0].message, "task 'task 1': 0:00:10 before due time")
        self.assertEqual(notifications[1].task, task)
        self.assertEqual(notifications[1].message, "task 'task 1' reached deadline")

    def test_recurrence(self):
        task = LocalTask()
        task.recurrence = Recurrent(RepeatType.DAILY, 3)

        recurrent = task.recurrence
        self.assertEqual(recurrent.mode, RepeatType.DAILY)
        self.assertEqual(recurrent.every, 3)


#     def test_repr(self):
#         task = LocalTask()
#         task.addSubItem( LocalTask() )
#         task.recurrence = Recurrent()
#         task.recurrence.setDaily()
#         task.reminderList = [ Reminder(1) ]
#         raw_data = task.__dict__
#         self.assertEqual( "", repr(raw_data) )


class TaskOccurrenceTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_date_current_subtask(self):
        task = LocalTask()
        startTime = datetime.datetime(2020, 10, 10)
        dueTime = startTime + timedelta(days=1)
        task.setOccurrence(startTime, dueTime)

        subtask = task.addSubTask()
        subtask.setDeadline()
        dueDateTime = task.dueDateTime - timedelta(days=7)
        subtask.setOccurrenceDue(dueDateTime)

        occurrence = task.currentOccurrence()
        self.assertEqual(occurrence.startCurrent, task.startDateTime)
        self.assertEqual(occurrence.dueCurrent, subtask.dueDateTime)

    def test_isTimedout(self):
        task = LocalTask()
        occurrence = task.currentOccurrence()
        self.assertEqual(occurrence.isTimedout(), False)

    def test_isReminded(self):
        task = LocalTask()
        dueDateTime = datetime.datetime.today() + datetime.timedelta(seconds=30)
        task.setOccurrenceDue(dueDateTime)

        occurrence = task.currentOccurrence()
        self.assertEqual(occurrence.isReminded(), False)

    def test_isReminded_reminded(self):
        task = LocalTask()
        dueDateTime = datetime.datetime.today() + datetime.timedelta(seconds=30)
        task.setOccurrenceDue(dueDateTime)

        reminder = Reminder()
        reminder.setTime(0, 300)
        task.addReminder(reminder)

        occurrence = task.currentOccurrence()
        self.assertEqual(occurrence.isReminded(), True)
