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

from enum import Enum, unique
from datetime import datetime, timedelta

# from hanlendar.domainmodel.task import Task


_LOGGER = logging.getLogger(__name__)


@unique
class TimePointType(Enum):
    #     Start = ()
    Due = ()  # pylint: disable=C0103


@unique
class RemainderDirectionType(Enum):
    Before = ()  # pylint: disable=C0103


#     After  = ()


class Notification:

    def __init__(self):
        self.notifyTime: datetime = None  ## time given in seconds since epoch
        self.message: str = None
        # ruff: noqa: UP037
        self.task: "Task" = None  # type: ignore[name-defined]  # noqa: F821

    def remainingSeconds(self) -> float:
        timeDiff = self.remainingTime()
        return timeDiff.total_seconds()

    def remainingTime(self) -> timedelta:
        currTime = datetime.today()
        return self.notifyTime - currTime

    def __str__(self):
        return f"[nt:{self.notifyTime} m:{self.message} t:{self.task.title}]"  # pylint: disable=E1101

    @staticmethod
    def sortByTime(notification):
        return notification.notifyTime


class Reminder:

    def __init__(self, days=None, timeOffset: timedelta = None, direction=None):
        self.timeOffset: timedelta = timeOffset
        self.direction: RemainderDirectionType = direction  ## not used?
        if days is not None:
            self.setDays(days)

    def setTime(self, days, seconds):
        self.setDays(days)
        self.setMillis(seconds * 1000)

    def setDays(self, days):
        if self.timeOffset is None:
            self.timeOffset = timedelta()
        remainTime = self.timeOffset % timedelta(days=1)
        remainSeconds = remainTime.total_seconds()
        self.timeOffset = timedelta(days=days, seconds=remainSeconds)

    def setMillis(self, millis):
        if self.timeOffset is None:
            self.timeOffset = timedelta()
        days = self.timeOffset.days
        self.timeOffset = timedelta(days=days, milliseconds=millis)

    # returns positive value
    def getOffset(self) -> timedelta:
        if self.timeOffset is None:
            return timedelta()
        return self.timeOffset

    # return pair [days, seconds]
    def splitTimeOffset(self):
        if self.timeOffset is None:
            return [0, 0]
        remainTime = self.timeOffset % timedelta(days=1)
        seconds = remainTime.total_seconds()
        return [self.timeOffset.days, seconds]

    def printPretty(self) -> str:
        offsetTime = self.timeOffset
        if offsetTime is None:
            offsetTime = timedelta()
        return print_timedelta(offsetTime) + " before due time"

    def __repr__(self):
        return f"Reminder( timeOffset={self.timeOffset!r}, direction={self.direction} )"

    @staticmethod
    def from_timedelta_string(value) -> "Reminder":
        fields = value.split(",")
        days = 0
        timeField = None
        if len(fields) > 1:
            timeField = fields[1]
            daysFields = fields[0].split(" ")
            days = int(daysFields[0])
        else:
            timeField = fields[0]
        timeField = timeField.strip()
        try:
            timePart = datetime.strptime(timeField, "%H:%M:%S")
            retObj = Reminder()
            retObj.timeOffset = timedelta(
                days=days,
                hours=timePart.hour,
                minutes=timePart.minute,
                seconds=timePart.second,
            )
        except ValueError as ex:
            _LOGGER.error("unable to load reminder from '%s' reason: %s", timeField, ex)
            return None
        return retObj


def print_timedelta(value: timedelta):
    s = ""
    secs = value.seconds
    days = value.days
    if secs != 0 or days == 0:
        mm, ss = divmod(secs, 60)
        hh, mm = divmod(mm, 60)
        s = f"{hh}:{mm:02d}:{ss:02d}"
    if days:

        def plural(n):
            return "s" if abs(n) != 1 else ""

        s = f"{days} day{plural(days)}, {s}" if s != "" else f"{days} day{plural(days)}"
    micros = value.microseconds
    if micros:
        s = s + f".{micros:06d}"
    return s
