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

from enum import Enum, unique, auto

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


_LOGGER = logging.getLogger(__name__)


@unique
class RepeatType(Enum):
    NEVER    = auto()
    DAILY    = auto()
    WEEKLY   = auto()
    MONTHLY  = auto()
    YEARLY   = auto()

    @classmethod
    def findByName(cls, name):
        for item in cls:
            if item.name == name:
                return item
        return None

    @classmethod
    def indexOf(cls, key):
        index = 0
        for item in cls:
            if item == key:
                return index
            if item.name == key:
                return index
            index = index + 1
        return -1


class Recurrent():

    def __init__(self, mode: RepeatType = None, every: int = None):
        if mode is None:
            mode = RepeatType.NEVER
        if every is None:
            every = 0
        if every < 0:
            every = 0

        self.mode: RepeatType = mode
        self.every            = every
        self.endDate: date    = None

    def setDaily(self, every=1):
        self.mode = RepeatType.DAILY
        self.every = every

    def setWeekly(self, every=1):
        self.mode = RepeatType.WEEKLY
        self.every = every

    def setMonthly(self, every=1):
        self.mode = RepeatType.MONTHLY
        self.every = every

    def getDateOffset( self ) -> relativedelta:
        if self.every < 1:
            return None

        if self.mode is RepeatType.NEVER:
            return None
        if self.mode is RepeatType.DAILY:
            return relativedelta( days=1 * self.every )
        if self.mode is RepeatType.WEEKLY:
            return relativedelta( days=7 * self.every )
        if self.mode is RepeatType.MONTHLY:
            return relativedelta( months=1 * self.every )
        if self.mode is RepeatType.YEARLY:
            return relativedelta( years=1 * self.every )

        _LOGGER.warn( "unhandled case" )
        return None

    def nextDate(self, currDate: date) -> date:
        if currDate is None:
            return None
        nextDate = currDate + self.getDateOffset()
        if self.endDate is None:
            return nextDate
        if nextDate > self.endDate:
            return None
        return nextDate

    def nextDateTime(self, currDate: datetime) -> datetime:
        if currDate is None:
            return None
        nextDate = currDate + self.getDateOffset()
        if self.endDate is None:
            return nextDate
        if nextDate.date() > self.endDate:
            return None
        return nextDate

    def hasEntryExact( self, referenceDate: date, entryDate: date ):
        if self.endDate is not None and self.endDate < entryDate:
            return False

        recurrentOffset: relativedelta = self.getDateOffset()
        if recurrentOffset is None:
            return False

        multiplicator = findMultiplicationAfter( referenceDate, entryDate, recurrentOffset )
        if multiplicator < 0:
            return False
        referenceDate += recurrentOffset * multiplicator
        if entryDate == referenceDate:
            return True
        return False

    def hasEntryInMonth( self, referenceDate: date, monthDate: date ):
        if self.endDate is not None and self.endDate < monthDate:
            return False

        recurrentOffset: relativedelta = self.getDateOffset()
        if recurrentOffset is None:
            return False

        multiplicator = findMultiplication( referenceDate, monthDate, recurrentOffset )
        if multiplicator < 1:
            return False

        intYear  = monthDate.year
        intMonth = monthDate.month

        nextMonthDate = monthDate.replace( day=1 ) + timedelta( days=31 )
        nextMonthDate = nextMonthDate.replace( day=1 )                      ## ensure first day of month
        referenceDate += recurrentOffset * (multiplicator - 1)
        while( referenceDate < nextMonthDate ):
            referenceDate += recurrentOffset
            if referenceDate.year == intYear and referenceDate.month == intMonth:
                return True
            multiplicator += 1

        return False

    def __repr__(self):
        return "[m:%s e:%s ed:%s]" % ( self.mode, self.every, self.endDate )


def findMultiplication( startDate: date, endDate: date, offset: relativedelta ) -> int:
    dateTD = endDate - startDate
    diffDays = dateTD.days

    ## calculate max possible offset in days
    ## 'maxDaysOffset' is always greater than 'offset' for all possible dates
    maxDaysOffset = offset.years * 366 + offset.months * 31 + offset.weeks * 7 + offset.days + 1

    ret = int(diffDays / maxDaysOffset)
    mul = int(ret / 2)

    startDate += offset * ret
    while( mul > 0 ):
        startDate += offset * mul
        if startDate < endDate:
            ret += mul
        else:
            mul = int(mul / 2)

    return ret


# returns: startDate + offset * multiplicator >= endDate
def findMultiplicationAfter( startDate: date, endDate: date, offset: relativedelta ) -> int:
    multiplicator = findMultiplication( startDate, endDate, offset )
    if multiplicator < 0:
        return multiplicator

    startDate += offset * (multiplicator - 1)
    while( startDate < endDate ):
        startDate += offset
        multiplicator += 1

    return multiplicator - 1
