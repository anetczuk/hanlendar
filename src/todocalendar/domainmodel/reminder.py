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

from datetime import timedelta
import copy

from enum import Enum, unique


@unique
class TimePointType(Enum):
#     Start = ()
    Due   = ()


@unique
class RemainderDirectionType(Enum):
    Before = ()
#     After  = ()


class Reminder():

    def __init__(self):
        self.timeOffset: timedelta              = None
        self.timePoint: TimePointType           = None
        self.direction: RemainderDirectionType  = None

    def setTime(self, days, seconds):
        self.setDays( days )
        self.setMillis( seconds * 1000 )

    def setDays(self, days):
        if self.timeOffset is None:
            self.timeOffset = timedelta()
        remainTime = self.timeOffset % timedelta( days=1 )
        remainSeconds = remainTime.total_seconds()
        self.timeOffset = timedelta( days=days, seconds=remainSeconds )

    def setMillis(self, millis):
        if self.timeOffset is None:
            self.timeOffset = timedelta()
        days = self.timeOffset.days
        self.timeOffset = timedelta( days=days, milliseconds=millis )

    # return pair [days, seconds]
    def splitTimeOffset(self):
        if self.timeOffset is None:
            return [ 0, 0 ]
        remainTime = self.timeOffset % timedelta( days=1 )
        seconds = remainTime.total_seconds()
        return [ self.timeOffset.days, seconds ]

    def printPretty(self) -> str:
        offsetTime = self.timeOffset
        if offsetTime is None:
            offsetTime = timedelta()
        output = str( offsetTime ) + " before due time"
        return output

    def __repr__(self):
        return "[t:%s p:%s d:%s]" % ( self.timeOffset, self.timePoint, self.direction )
