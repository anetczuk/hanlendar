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

from datetime import datetime, timedelta

from todocalendar.domainmodel.reminder import Reminder, Notification


class NotificationTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_remainingSeconds_positive(self):
        notify = Notification()
        currTime = datetime.today() + timedelta( seconds=5 )
        notify.notifyTime = currTime
        secs = notify.remainingSeconds()
        self.assertGreater( secs, 0 )

    def test_remainingSeconds_negative(self):
        notify = Notification()
        currTime = datetime.today() - timedelta( seconds=5 )
        notify.notifyTime = currTime
        secs = notify.remainingSeconds()
        self.assertLess( secs, 0 )


class ReminderTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_setDays(self):
        reminder = Reminder()
        reminder.setMillis( 2000 )
        reminder.setDays( 3 )

        time = reminder.splitTimeOffset()
        self.assertEqual( time[0], 3 )
        self.assertEqual( time[1], 2 )

    def test_setMillis(self):
        reminder = Reminder()
        reminder.setDays( 3 )
        reminder.setMillis( 2000 )

        time = reminder.splitTimeOffset()
        self.assertEqual( time[0], 3 )
        self.assertEqual( time[1], 2 )

    def test_setMillis_big(self):
        reminder = Reminder()
        reminder.setDays( 3 )
        millis = 2000 + 2 * 1000 * 60 * 60 * 24
        reminder.setMillis( millis )

        time = reminder.splitTimeOffset()
        self.assertEqual( time[0], 5 )
        self.assertEqual( time[1], 2 )

    def test_printPretty(self):
        reminder = Reminder()
        reminder.setDays( 3 )

        text = reminder.printPretty()
        self.assertEqual( text, "3 days before due time" )

    def test_printPretty_zero(self):
        reminder = Reminder()

        text = reminder.printPretty()
        self.assertEqual( text, "0:00:00 before due time" )
