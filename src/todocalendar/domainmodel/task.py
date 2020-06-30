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

from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta

from .reminder import Reminder, Notification

from typing import List
from todocalendar.domainmodel.recurrent import RepeatType


_LOGGER = logging.getLogger(__name__)


class Task():
    """Task is entity that lasts over time."""

    def __init__(self):
        self.title                          = ""
        self.description                    = ""
        self._completed                     = 0        ## in range [0..100]
        self.priority                       = 10       ## lower number, greater priority
        self._startDate: datetime           = None
        self._dueDate: datetime             = None
        self.reminderList: List[Reminder]   = None
        self._recurrence                    = None
        self._recurrentStartDate: datetime  = None
        self._recurrentDueDate: datetime    = None

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value):
        self.setCompleted( value )

    def setCompleted(self, value=100):
        if value < 0:
            value = 0
        elif value > 100:
            value = 100
        if self._progressRecurrence() is True:
            # completed -- next occurrence
            self._completed = 0
        else:
            self._completed = value

    def isCompleted(self):
        return self._completed >= 100

    @property
    def startDate(self):
        if self._recurrence is not None:
            return self._recurrentStartDate
        return self._startDate

    @startDate.setter
    def startDate(self, value):
        self._startDate = value
        if self._recurrence is not None:
            self._recurrentStartDate = self._startDate
        
    @property
    def dueDate(self):
        if self._recurrence is not None:
            return self._recurrentDueDate
        return self._dueDate

    @dueDate.setter
    def dueDate(self, value):
        self._dueDate = value
        if self._recurrence is not None:
            self._recurrentDueDate = self._dueDate

    @property
    def recurrence(self):
        return self._recurrence

    @recurrence.setter
    def recurrence(self, value):
        if self._recurrence is None and value is not None:
            self._recurrentStartDate = self._startDate
            self._recurrentDueDate = self._dueDate
        self._recurrence = value

    def getReferenceDateTime(self) -> datetime:
        if self.startDate is None:
            ## deadline case
            return self.dueDate
        return self.startDate

    def setDefaultDateTime(self, start: datetime ):
        self.startDate = start
        self.dueDate = self.startDate + timedelta( hours=1 )

    def setDefaultDate(self, startDate: date):
        start = datetime.combine( startDate, time(10, 0, 0) )
        self.setDefaultDateTime( start )

    def setDeadline(self):
        self.startDate = None

    def setDeadlineDateTime(self, due: datetime ):
        self.startDate = None
        self.dueDate = due

    def setDeadlineDate(self, dueDate: date):
        due = datetime.combine( dueDate, time(10, 0, 0) )
        self.setDeadlineDateTime( due )

    def hasEntry( self, entriesDate: date ):
        currDate = self.getReferenceDateTime().date()
        if currDate == entriesDate:
            return True
        if self._recurrence is None:
            return False

        while( currDate < entriesDate ):
            currDate = self._recurrence.nextDate( currDate )
            if currDate is None:
                ## recurrence end date reached
                return False
            if currDate == entriesDate:
                return True

        return False

    def getNotifications(self):
        if self.dueDate is None:
            return list()
        currTime = datetime.today()
        ret = list()
        if self.dueDate > currTime:
            notif = Notification()
            notif.notifyTime = self.dueDate
            notif.task = self
            notif.message = "task '%s' reached deadline" % self.title
            ret.append( notif )

        if self.reminderList is None:
            return ret

        for reminder in self.reminderList:
            notif = Notification()
            notif.notifyTime = self.dueDate - reminder.getOffset()
            notif.task = self
            notif.message = reminder.printPretty()
            ret.append( notif )

        ret.sort( key=Notification.sortByTime )
        return ret

    def isTimedout(self):
        currTime = datetime.today()
        return currTime > self.dueDate

    def printRecurrent(self) -> str:
        if self._recurrence is None:
            return "None"
        refDate = self.getReferenceDateTime()
        nextRepeat = self._recurrence.nextDateTime( refDate )
        if nextRepeat is None:
            return "None"
        dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
        return dateText

    def __str__(self):
        return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s rsd:%s rdd:%s]" % ( 
                                        self.title, self.description, self._completed, self.priority,
                                        self.startDate, self.dueDate,
                                        self.reminderList, self._recurrence,
                                        self._recurrentStartDate, self._recurrentDueDate )

    def _progressRecurrence(self) -> bool:
        if self._recurrence is None:
            return False
        nextDue = self._recurrence.nextDateTime( self._recurrentDueDate )
        if nextDue is None:
            return False
        self._recurrentDueDate = nextDue
        self._recurrentStartDate = self._recurrence.nextDateTime( self._recurrentStartDate )
        return True
