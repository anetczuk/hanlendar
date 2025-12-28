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

import datetime
from dateutil.relativedelta import relativedelta

from hanlendar import persist
from hanlendar.domainmodel.utils import DateDateTime


_LOGGER = logging.getLogger(__name__)


@unique
class RepeatType(Enum):
    NEVER = auto()
    DAILY = auto()
    WEEKLY = auto()
    MONTHLY = auto()
    YEARLY = auto()
    ASPARENT = auto()

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
class RepeatUntilMode(Enum):
    FOREVER = auto()
    OCCURENCES = auto()
    UNTIL_DATE = auto()


class Recurrent(persist.Versionable):

    ##  0: add versioning
    ##  1: added 'exception_dates', 'occurences', 'occurenceMode'
    ##  2: do nothing
    ##  3: added 'weekday', 'monthweek', 'monthday', 'month'
    _class_version = 3

    def __init__(self, mode: RepeatType = None, every: int = None, endDate: datetime.date = None):
        super().__init__()

        if mode is None:
            mode = RepeatType.NEVER
        if every is None:
            every = 0
        every = max(every, 0)

        self.mode: RepeatType = mode  ## FREQ, list
        self.every: int = every  ## INTERVAL
        self.weekday: list[int] = None  ## for WEEKLY and MONTHLY, indicates days of week
        self.monthweek: list[int] = (
            None  ## for MONTHLY, indicates weekday in month (e.g second Sunday or last Monday), 0 means Monday
        )
        self.monthday: list[int] = (
            None  ## for MONTHLY, indicates day of month, eg. 1st, 12nd, 24th, 1 means first day of month
        )
        self.month: list[int] = None  ## for YEARLY, indicates month of year, eg. 1st, 2nd, 6th, 1 means January

        self.occurenceMode: RepeatUntilMode = None  ## None means "forever"
        self.occurences: int = None  ## COUNT (number of occurrences of item)
        self.endDate: datetime.date = endDate  ## UNTIL

        self.exception_dates: list[DateDateTime] = []

    def _convertstate_(self, state_dict, state_version):
        _LOGGER.info("converting object from version %s to %s", state_version, self._class_version)

        if state_version is None:
            state_version = -1

        state_version = max(state_version, 0)

        if state_version == 0:
            state_dict["exception_dates"] = None
            state_dict["occurenceMode"] = None
            state_dict["occurences"] = None
            if state_dict["endDate"] is not None:
                state_dict["occurenceMode"] = RepeatUntilMode.UNTIL_DATE
            state_version += 1

        if state_version == 1:
            ## do nothing
            state_version += 1

        if state_version == 2:
            state_dict["weekday"] = None
            state_dict["monthweek"] = None
            state_dict["monthday"] = None
            state_dict["month"] = None
            state_version += 1

        return state_dict

    def _key(self):
        return (self.mode, self.every, self.endDate)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._key() == other._key()

    def __repr__(self):
        return f"Recurrent( mode={self.mode}, every={self.every}, endDate={self.endDate} )"

    def isValid(self):
        if self.mode == RepeatType.NEVER:
            return False
        return self.every > 0

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

    def getDateOffset(self) -> relativedelta:
        if self.every < 1:
            return None

        if self.mode is RepeatType.NEVER:
            return None
        if self.mode is RepeatType.ASPARENT:
            return None
        if self.mode is RepeatType.DAILY:
            return relativedelta(days=1 * self.every)
        if self.mode is RepeatType.WEEKLY:
            return relativedelta(days=7 * self.every)
        if self.mode is RepeatType.MONTHLY:
            return relativedelta(months=1 * self.every)
        if self.mode is RepeatType.YEARLY:
            return relativedelta(years=1 * self.every)

        _LOGGER.warning("unhandled case")
        return None

    def isEnd(self, currDate: datetime.date) -> bool:
        if currDate is None:
            return False
        if self.endDate is None:
            return False
        return currDate > self.endDate

    def nextDateTime(
        self,
        currDate: DateDateTime,
        offset: int = 1,
    ) -> DateDateTime:
        if currDate is None:
            return None
        dateOffset = self.getDateOffset()
        if dateOffset is None:
            return None
        nextDate = currDate + dateOffset * offset
        if self.endDate is None:
            return nextDate
        if isinstance(nextDate, datetime.datetime):
            if nextDate.date() > self.endDate:
                return None
        elif nextDate > self.endDate:
            return None
        return nextDate

    def findRecurrentOffset(self, referenceDate: datetime.date, targetDate: datetime.date) -> int:
        offset = self.getDateOffset()
        return find_multiplication(referenceDate, targetDate, offset)


def find_multiplication(startDate: datetime.date, endDate: datetime.date, offset: relativedelta) -> int:
    dateTD = endDate - startDate
    diffDays = dateTD.days

    ## calculate max possible offset in days
    ## 'maxDaysOffset' is always greater than 'offset' for all possible dates
    maxDaysOffset = offset.years * 366 + offset.months * 31 + offset.weeks * 7 + offset.days + 1

    ret = int(diffDays / maxDaysOffset)
    mul = int(ret / 2)
    mul = max(mul, 1)  ## handle case when 'maxDaysOffset' is greater than 'offset'

    startDate += offset * ret
    while mul > 0:
        startDate += offset * mul
        if startDate <= endDate:
            ret += mul
        else:
            mul = int(mul / 2)

    return ret


# returns: startDate + offset * multiplicator >= endDate
def find_multiplication_after(startDate: datetime.date, endDate: datetime.date, offset: relativedelta) -> int:
    multiplicator = find_multiplication(startDate, endDate, offset)
    if multiplicator < 0:
        return multiplicator

    startDate += offset * (multiplicator - 1)
    while startDate < endDate:
        startDate += offset
        multiplicator += 1

    return multiplicator - 1
