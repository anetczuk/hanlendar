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

from todocalendar.domainmodel.manager import Manager
import datetime


class ManagerTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_hasEntries_empty(self):
        manager = Manager()
        taskDate = datetime.date( 2020, 5, 17 )
        self.assertEqual( manager.hasEntries(taskDate), False )

    def test_hasEntries_entries(self):
        manager = Manager()
        taskDate = datetime.date( 2020, 5, 17 )
        manager.addTask( taskDate, "xxx" )
        self.assertEqual( manager.hasEntries(taskDate), True )

    def test_getEntries_entries(self):
        manager = Manager()

        taskDate1 = datetime.date( 2020, 5, 17 )
        manager.addTask( taskDate1, "task1" )
        taskDate2 = datetime.date( 2020, 5, 18 )
        manager.addTask( taskDate2, "task2" )

        entries = manager.getEntries(taskDate2)
        self.assertEqual( len(entries), 1 )
        self.assertEqual( entries[0], "task2" )