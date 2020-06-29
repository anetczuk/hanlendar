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

from todocalendar.domainmodel.task import Task
from todocalendar.domainmodel.reminder import Reminder


class TaskTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

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
        task.reminderList = list()
        task.reminderList.append( reminder )

        notifications = task.getNotifications()
        self.assertEqual( len(notifications), 2 )
        self.assertEqual( notifications[0].task, task )
        self.assertEqual( notifications[0].message, "0:00:10 before due time" )
        self.assertEqual( notifications[1].task, task )
        self.assertEqual( notifications[1].message, "task 'task 1' reached deadline" )
