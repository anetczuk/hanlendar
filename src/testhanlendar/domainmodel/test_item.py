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

import copy

from hanlendar.domainmodel.item import CommonData
from hanlendar.domainmodel.recurrent import Recurrent
from hanlendar.domainmodel.reminder import Reminder


class CommonDataTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_compare_self(self):
        item = CommonData()

        # ruff: noqa: PLR0124
        self.assertTrue(item == item)  # pylint: disable=R0124
        # ruff: noqa: PLR0124
        self.assertTrue(item is item)  # pylint: disable=R0124
        # ruff: noqa: PLR0124
        self.assertFalse(item != item)  # pylint: disable=R0124
        self.assertEqual(item, item)

    def test_compare_copy(self):
        item_01 = CommonData()
        item_02 = copy.deepcopy(item_01)

        self.assertTrue(item_01 == item_02)
        self.assertFalse(item_01 is item_02)
        self.assertFalse(item_01 != item_02)
        self.assertEqual(item_01, item_02)

    def test_compare_equal(self):
        item_01 = CommonData()
        item_02 = CommonData()
        item_02.UID = item_01.UID
        item_02.createDate = item_01.createDate
        item_02.lastModifiedDate = item_01.lastModifiedDate

        self.assertTrue(item_01 == item_02)
        self.assertFalse(item_01 is item_02)
        self.assertFalse(item_01 != item_02)
        self.assertEqual(item_01, item_02)

    def test_compare_diff(self):
        item_01 = CommonData()
        item_02 = CommonData()
        item_02.title = item_01.title + "xxx"

        self.assertFalse(item_01 == item_02)
        self.assertFalse(item_01 is item_02)
        self.assertTrue(item_01 != item_02)
        self.assertNotEqual(item_01, item_02)

    def test_in_self(self):
        item = CommonData()
        item_set = {item}

        self.assertTrue(item in item_set)
        self.assertFalse(item not in item_set)
        self.assertIn(item, item_set)

    def test_in_copy(self):
        item_01 = CommonData()
        item_01.recurrence = Recurrent()
        item_01.reminderList = [Reminder()]
        item_set = {item_01}
        item_02 = copy.deepcopy(item_01)

        self.assertTrue(item_02 in item_set)
        self.assertFalse(item_02 not in item_set)
        self.assertIn(item_02, item_set)

    def test_in_diff_01(self):
        item_01 = CommonData()
        item_set = {item_01}
        item_02 = CommonData()
        item_02.title = f"{item_01.title}_xxx"

        self.assertFalse(item_02 in item_set)
        self.assertTrue(item_02 not in item_set)
        self.assertNotIn(item_02, item_set)

    def test_in_diff_02(self):
        item_01 = CommonData()
        item_01.recurrence = Recurrent()
        item_set = {item_01}

        item_02 = copy.deepcopy(item_01)
        item_02.recurrence.every = item_01.recurrence.every + 1

        self.assertFalse(item_02 in item_set)
        self.assertTrue(item_02 not in item_set)
        self.assertNotIn(item_02, item_set)

    def test_in_diff_03(self):
        item_01 = CommonData()
        item_01.reminderList = [Reminder()]
        item_set = {item_01}

        item_02 = copy.deepcopy(item_01)
        item_02.reminderList[0].action = f"{item_01.reminderList[0].action}_xxx"

        self.assertFalse(item_02 in item_set)
        self.assertTrue(item_02 not in item_set)
        self.assertNotIn(item_02, item_set)
