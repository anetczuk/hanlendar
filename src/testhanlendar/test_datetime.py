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

from testhanlendar.datetimetoday import get_today

from testhanlendar.mock_datetime import get_mock_date, get_mock_datetime


class DateTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_today_mock_with(self):
        target = datetime.date(2009, 1, 1)
        self.assertLess( target, datetime.date.today() )

        with get_mock_date(target):
            today = datetime.date.today()
            self.assertEqual( target, today )
            self.assertTrue( isinstance(today, datetime.date) )

        self.assertLess( target, datetime.date.today() )

    def test_today_mock_start(self):
        target = datetime.date(2009, 1, 1)
        self.assertLess( target, datetime.date.today() )

        mockObj = get_mock_date(target)
        mockObj.start()
        today = datetime.date.today()
        self.assertEqual( target, today )
        self.assertTrue( isinstance(today, datetime.date) )
        mockObj.stop()

        self.assertLess( target, datetime.date.today() )


class DateTimeTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_today_mock_with(self):
        target = datetime.datetime(2009, 1, 1)
        self.assertLess( target, datetime.datetime.today() )

        with get_mock_datetime(target):
            today = datetime.datetime.today()
            self.assertEqual( target, today )
            self.assertTrue( isinstance(today, datetime.datetime) )

        self.assertLess( target, datetime.datetime.today() )

    def test_today_mock_start(self):
        target = datetime.datetime(2009, 1, 1)
        self.assertLess( target, datetime.datetime.today() )

        mockObj = get_mock_datetime(target)
        mockObj.start()
        today = datetime.datetime.today()
        self.assertEqual( target, today )
        self.assertTrue( isinstance(today, datetime.datetime) )
        mockObj.stop()

        self.assertLess( target, datetime.datetime.today() )

    def test_get_today_mock(self):
        target = datetime.datetime(2009, 1, 1)
        self.assertLess( target, datetime.datetime.today() )

        with get_mock_datetime(target):
            today = get_today()
            self.assertEqual( target, today )
