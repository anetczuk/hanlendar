# MIT License
#
# Copyright (c) 2025 Arkadiusz Netczuk <dev.arnet@gmail.com>
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

import logging

# import datetime
# from dateutil.relativedelta import relativedelta
#
# from hanlendar.domainmodel.recurrent import find_multiplication_after


_LOGGER = logging.getLogger(__name__)


class CalendarData:

    DEFAULT_LABEL: str = "(local default)"

    def __init__(self):
        ## calendar_label: str, calendar_id: str, enabled: bool
        self.items: list[tuple[str, str, bool]] = [(CalendarData.DEFAULT_LABEL, None, True)]

    def getItems(self) -> list[tuple[str, str, bool]]:
        return list(self.items)  ## copy list

    def addCalendar(self, cal_label, cal_id: str, *, enabled: bool):
        for item in self.items:
            if item[1] == cal_id:
                ## item already exists
                return
        self.items.append((cal_label, cal_id, enabled))

    def isEnabled(self, calendar_id: str):
        item = self._findCalendarItem(calendar_id)
        if item is None:
            return True
        return item[2]

    def _findCalendarItem(self, calendar_id: str):
        for item in self.items:
            if item[1] == calendar_id:
                return item
        return None
