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

from datetime import date

from hanlendar.domainmodel.recurrent import Recurrent, RepeatType


class RepeatTypeTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_values(self):
        self.assertEqual( RepeatType.NEVER.value, 1 )
        self.assertEqual( RepeatType.DAILY.value, 2 )
        self.assertEqual( RepeatType.WEEKLY.value, 3 )
        self.assertEqual( RepeatType.MONTHLY.value, 4 )
        self.assertEqual( RepeatType.YEARLY.value, 5 )
        self.assertEqual( RepeatType.ASPARENT.value, 6 )


class RecurrentTest(unittest.TestCase):
    def setUp(self):
        ## Called before testfunction is executed
        pass

    def tearDown(self):
        ## Called after testfunction was executed
        pass

    def test_findRecurrentOffset(self):
        recurrent = Recurrent()
        recurrent.setYearly( 1 )

        refDate    = date( 2020, 5, 2 )
        targetDate = refDate + recurrent.getDateOffset()
        offset = recurrent.findRecurrentOffset(refDate, targetDate)

        self.assertEqual( offset, 1 )
