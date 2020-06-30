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

from datetime import date
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

    def getDateOffset( self ):
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

    def __repr__(self):
        return "[m:%s e:%s ed:%s]" % ( self.mode, self.every, self.endDate )
