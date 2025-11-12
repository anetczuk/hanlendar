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

import logging
import datetime
from dateutil.relativedelta import relativedelta

from hanlendar.domainmodel.recurrent import find_multiplication_after


_LOGGER = logging.getLogger(__name__)


class DateRange:

    def __init__(self, start=None, end=None):
        self.start: datetime.date = start
        self.end: datetime.date = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        message = "bad index: 0 or 1 allowed"
        raise IndexError(message)

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateRange(start, end)

    ## in keyword
    def __contains__(self, entryDate: datetime.date):
        if self.start is not None and entryDate < self.start:
            return False
        return not entryDate > self.end

    def isNormalized(self):
        if self.start is None:
            return False
        return self.end is not None

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def isInMonth(self, monthDate: datetime.date):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        return currDate.year == monthDate.year and currDate.month == monthDate.month

    def __str__(self):
        return f"[s:{self.start} e:{self.end}]"


## ========================================================================


class DateTimeRange:

    def __init__(self, start=None, end=None):
        self.start: datetime.datetime = start
        self.end: datetime.datetime = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        message = "bad index: 0 or 1 allowed"
        raise IndexError(message)

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateTimeRange(start, end)

    ## in keyword
    def __contains__(self, entryDate: datetime.datetime):
        if self.start is not None and entryDate < self.start:
            return False
        return not (self.end is not None and entryDate > self.end)

    def _key(self):
        return (self.start, self.end)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() == other._key()

    def __str__(self):
        return f"[s:{self.start} e:{self.end}]"

    def __repr__(self):
        return f"[DTR {self.start} {self.end}]"

    def get_raw(self):
        return (self.start, self.end)

    def dateRange(self) -> DateRange:
        start = None
        if self.start is not None:
            start = self.start.date()
        end = None
        if self.end is not None:
            end = self.end.date()
        return DateRange(start, end)

    def isNormalized(self):
        if self.start is None:
            return False
        return self.end is not None

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def isInMonth(self, monthDate: datetime.datetime):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate is None:
            return False
        return currDate.year == monthDate.year and currDate.month == monthDate.month

    def isInPastMonths(self, monthDate: datetime.datetime):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate is None:
            return False
        if currDate.year < monthDate.year:
            return True
        return currDate.year == monthDate.year and currDate.month < monthDate.month


## ========================================================================


class TaskOccurrence:
    """Occurrences of task.

    Regular task has only one occurrence.
    Recurrent tasks has many occurrences.
    """

    def __init__(self, task, datetime_range: DateTimeRange = None):
        if task is None:
            raise TypeError
        self.task = task
        if datetime_range is None:
            datetime_range = task.getDateTimeRange()
        self._dateRange = datetime_range

    def __str__(self):
        return f"[t:{self.task.title} {self.task.dueDateTime} range:{self.dateRange}]"

    def isValid(self):
        return self.dateRange is not None

    @property
    def title(self):
        return self.task.title

    @property
    def priority(self):
        return self.task.priority

    @property
    def completed(self):
        return self.task.completed

    @property
    def start(self):
        return self.dateRange.start

    @property
    def startCurrent(self):
        subOccurrences = self.task.subOccurrences()
        retDate = self.start
        for currItem in subOccurrences:
            if currItem.start is None:
                continue
            if retDate is None:
                retDate = currItem.start
            else:
                retDate = min(currItem.start, retDate)
        return retDate

    @property
    def due(self):
        return self.dateRange.end

    @property
    def dueCurrent(self):
        subOccurrences = self.task.subOccurrences()
        retDate = self.due
        for currItem in subOccurrences:
            if currItem.due is None:
                continue
            retDate = currItem.due if retDate is None else min(currItem.due, retDate)
        return retDate

    def isCompleted(self):
        if self.dateRange.end < self.task.dueDateTime:
            return True
        return self.task.isCompleted()

    def isTimedout(self):
        if self.dateRange.end is None:
            return False
        currTime = datetime.datetime.today()
        return currTime > self.dateRange.end

    def isReminded(self):
        if self.dateRange.end is None:
            return False
        retOffset = self.task.getReminderGreatest()
        if retOffset is None:
            return False
        currTime = datetime.datetime.today()
        notifTime = self.dateRange.end - retOffset
        return not notifTime > currTime

    @property
    def dateRange(self):
        if hasattr(self, "_dateRange") and self._dateRange is not None:
            return self._dateRange
        return None

    def getFirstDateTime(self):
        return self.task.getFirstDateTime()

    def isInMonth(self, monthDate: datetime.date):
        return self.dateRange.isInMonth(monthDate)

    def isInPastMonths(self, monthDate: datetime.date):
        return self.dateRange.isInPastMonths(monthDate)

    def calculateTimeSpan(self, entryDate: datetime.date):
        startDate = self.task.startDateTime
        endDate = self.task.dueDateTime
        ret = calc_time_span(entryDate, startDate, endDate)
        if ret is not None:
            return ret

        recurrence = self.task.getAppliedRecurrence()
        if recurrence is None:
            return [0, 1]
        recurrentDateOffset: relativedelta = recurrence.getDateOffset()
        if recurrentDateOffset is None:
            return [0, 1]

        multiplicator = find_multiplication_after(endDate.date(), entryDate, recurrentDateOffset)
        if multiplicator < 0:
            return [0, 1]
        endDate += recurrentDateOffset * multiplicator
        if startDate is not None:
            startDate += recurrentDateOffset * multiplicator
        ret = calc_time_span(entryDate, startDate, endDate)
        if ret is not None:
            return ret
        return [0, 1]

    @staticmethod
    def sortByDates(entry):
        ## entry.dateRange[0] can be None
        if entry.dateRange[0] is None:
            return (entry.dateRange[1],)
        return (entry.dateRange[1], entry.dateRange[0])


## ========================================================================
## ========================================================================


def calc_time_span(entryDate: datetime.date, start: datetime.datetime, end: datetime.datetime):
    startFactor = 0.0
    if start is not None:
        startDate = start.date()
        if entryDate < startDate:
            return None
        if entryDate == startDate:
            midnight = datetime.datetime.combine(entryDate, datetime.datetime.min.time())
            startDiff = start - midnight
            daySecs = datetime.timedelta(days=1).total_seconds()
            startFactor = startDiff.total_seconds() / datetime.timedelta(days=1).total_seconds()
    dueFactor = 1.0
    if end is not None:
        endDate = end.date()
        if entryDate > endDate:
            return None
        if entryDate == endDate:
            midnight = datetime.datetime.combine(entryDate, datetime.datetime.min.time())
            startDiff = end - midnight
            daySecs = datetime.timedelta(days=1).total_seconds()
            dueFactor = startDiff.total_seconds() / daySecs
    return [startFactor, dueFactor]
