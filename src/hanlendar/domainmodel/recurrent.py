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

from datetime import date, datetime
from dateutil.relativedelta import relativedelta


_LOGGER = logging.getLogger(__name__)


@unique
class RepeatType(Enum):
    NEVER     = auto()
    DAILY     = auto()
    WEEKLY    = auto()
    MONTHLY   = auto()
    YEARLY    = auto()
    ASPARENT  = auto()

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


@unique
class RecurrentField(Enum):
    MODE     = auto()
    STEP     = auto()
    ENDDATE  = auto()

    @classmethod
    def findByName(cls, name, defaultValue=None):
        for item in cls:
            if item.name == name:
                return item
        return defaultValue

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

    def __init__(self, mode: RepeatType = None, every: int = None, endDate: date = None):
        if mode is None:
            mode = RepeatType.NEVER
        if every is None:
            every = 0
        if every < 0:
            every = 0

        self.mode: RepeatType = mode
        self.every: int       = every
        self.endDate: date    = endDate

    def isValid(self):
        if self.mode == RepeatType.NEVER:
            return False
        if self.every < 1:
            return False
        return True

    def isAsParent(self):
        return self.mode == RepeatType.ASPARENT

    def setDaily(self, every=1):
        self.mode = RepeatType.DAILY
        self.every = every

    def setWeekly(self, every=1):
        self.mode = RepeatType.WEEKLY
        self.every = every

    def setMonthly(self, every=1):
        self.mode = RepeatType.MONTHLY
        self.every = every

    def setYearly(self, every=1):
        self.mode = RepeatType.YEARLY
        self.every = every

    def getDateOffset( self ) -> relativedelta:
        if self.every < 1:
            return None

        if self.mode is RepeatType.NEVER:
            return None
        if self.mode is RepeatType.ASPARENT:
            return None
        if self.mode is RepeatType.DAILY:
            return relativedelta( days=1 * self.every )
        if self.mode is RepeatType.WEEKLY:
            return relativedelta( days=7 * self.every )
        if self.mode is RepeatType.MONTHLY:
            return relativedelta( months=1 * self.every )
        if self.mode is RepeatType.YEARLY:
            return relativedelta( years=1 * self.every )

        _LOGGER.warning( "unhandled case" )
        return None

    def isEnd(self, currDate: date) -> bool:
        if currDate is None:
            return False
        if self.endDate is None:
            return False
        if currDate > self.endDate:
            return True
        return False

    def nextDateTime(self, currDate: datetime) -> datetime:
        if currDate is None:
            return None
        dateOffset = self.getDateOffset()
        if dateOffset is None:
            return None
        nextDate = currDate + dateOffset
        if self.endDate is None:
            return nextDate
        if nextDate.date() > self.endDate:
            return None
        return nextDate

    def findRecurrentOffset(self, referenceDate: date, targetDate: date) -> int:
        offset = self.getDateOffset()
        return find_multiplication( referenceDate, targetDate, offset )

    def __eq__( self, other: 'Recurrent' ):
        if not isinstance(other, Recurrent):
            ## don't attempt to compare against unrelated types
            return NotImplemented

        return self.mode == other.mode and self.every == other.every and self.endDate == other.endDate

    def __repr__(self):
        return "Recurrent( mode=%s, every=%s, endDate=%s )" % ( self.mode, self.every, self.endDate )
        ## return "[m:%s e:%s ed:%s]" % ( self.mode, self.every, self.endDate )


def find_multiplication( startDate: date, endDate: date, offset: relativedelta ) -> int:
    dateTD = endDate - startDate
    diffDays = dateTD.days

    ## calculate max possible offset in days
    ## 'maxDaysOffset' is always greater than 'offset' for all possible dates
    maxDaysOffset = offset.years * 366 + offset.months * 31 + offset.weeks * 7 + offset.days + 1

    ret = int(diffDays / maxDaysOffset)
    mul = int(ret / 2)
    mul = max( mul, 1 )     ## handle case when 'maxDaysOffset' is greater than 'offset'

    startDate += offset * ret
    while mul > 0:
        startDate += offset * mul
        if startDate <= endDate:
            ret += mul
        else:
            mul = int(mul / 2)

    return ret


# returns: startDate + offset * multiplicator >= endDate
def find_multiplication_after( startDate: date, endDate: date, offset: relativedelta ) -> int:
    multiplicator = find_multiplication( startDate, endDate, offset )
    if multiplicator < 0:
        return multiplicator

    startDate += offset * (multiplicator - 1)
    while startDate < endDate:
        startDate += offset
        multiplicator += 1

    return multiplicator - 1
