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
from typing import List
import math

from .reminder import Reminder, Notification

from hanlendar import persist
from hanlendar.domainmodel import recurrent
from hanlendar.domainmodel.recurrent import RepeatType, Recurrent


_LOGGER = logging.getLogger(__name__)


class DateRange():

    def __init__(self, start=None, end=None ):
        self.start: date = start
        self.end:   date = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        raise IndexError( "bad index: 0 or 1 allowed" )

    ## + (plus) operator
    def __add__(self, dateOffset):
        return DateRange( self.start + dateOffset, self.end + dateOffset )

    ## in keyword
    def __contains__(self, entryDate: date):
        if self.start is not None and entryDate < self.start:
            return False
        if entryDate > self.end:
            return False
        return True

    def isNormalized(self):
        if self.start is None:
            return False
        if self.end is None:
            return False
        return True

    def normalize(self):
        if self.start is None:
            self.start = self.end

    def __str__(self):
        return "[s:%s e:%s]" % ( self.start, self.end )


class Task( persist.Versionable ):
    """Task is entity that lasts over time."""

    _class_version = 0

    def __init__(self, title="" ):
        self.title                          = title
        self.description                    = ""
        self._completed                     = 0        ## in range [0..100]
        self.priority                       = 10       ## lower number, greater priority
        self._startDate: datetime           = None
        self._dueDate: datetime             = None
        self.reminderList: List[Reminder]   = None
        self._recurrence: Recurrent         = None
        self._recurrentStartDate: datetime  = None
        self._recurrentDueDate: datetime    = None

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )
        if dictVersion_ is None:
            self.__dict__ = dict_
            return
        self.__dict__ = dict_

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
        if value == 100 and self._progressRecurrence() is True:
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
        value = ensureDateTime( value )
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
        value = ensureDateTime( value )
        self._dueDate = value
        if self._recurrence is not None:
            self._recurrentDueDate = self._dueDate

    @property
    def recurrence(self) -> Recurrent:
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

    def getFirstDateTime(self) -> datetime:
        if self.dueDate is None:
            return None
        minDate = self.dueDate
        if self.startDate is not None and self.startDate < minDate:
            minDate = self.startDate
        remindDate = self.getReminderFirstDate()
        if remindDate is not None and remindDate < minDate:
            minDate = remindDate
        return minDate

    def getDateRange(self) -> DateRange:
        startDate = None
        endDate   = None
        if self.startDate is not None:
            startDate = self.startDate.date()
        if self.dueDate is not None:
            endDate = self.dueDate.date()
        return DateRange(startDate, endDate)

    def getDateRangeNormalized(self) -> DateRange:
        dateRange: DateRange = self.getDateRange()
        dateRange.normalize()
        if dateRange[1] is None:
            return None
        return dateRange

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

    def calculateTimeSpan(self, entryDate: date):
        ret = calcTimeSpan( entryDate, self.startDate, self.dueDate )
        if ret is not None:
            return ret

        if self.recurrence is None:
            return [0, 1]
        recurrentOffset: relativedelta = self.recurrence.getDateOffset()
        if recurrentOffset is None:
            return [0, 1]

        endDate = self.dueDate
        multiplicator = recurrent.findMultiplicationAfter( endDate.date(), entryDate, recurrentOffset )
        if multiplicator < 0:
            return [0, 1]
        endDate += recurrentOffset * multiplicator
        startDate = self.startDate
        if startDate is not None:
            startDate += recurrentOffset * multiplicator
        ret = calcTimeSpan( entryDate, startDate, endDate )
        if ret is not None:
            return ret
        return [0, 1]

    def hasTaskOccurrenceExact( self, entryDate: date ):
        refDate = self.getReferenceDateTime()
        if refDate is None:
            return False
        currDate = refDate.date()
        if currDate == entryDate:
            return True

        if self._recurrence is None:
            return False

        return self.recurrence.hasTaskOccurrenceExact( currDate, entryDate )

    def hasTaskOccurrenceInMonth( self, month: date ):
        refDate = self.getReferenceDateTime()
        if refDate is None:
            return False
        currDate = refDate.date()
        if currDate.year == month.year and currDate.month == month.month:
            return True
        if self._recurrence is None:
            return False
        return self._recurrence.hasTaskOccurrenceInMonth( currDate, month )

    def getTaskOccurrenceForDate(self, entryDate: date):
        dateRange: DateRange = self.getDateRangeNormalized()
        if dateRange is None:
            return None
        if entryDate in dateRange:
            return TaskOccurrence( self )
        if self.recurrence is None:
            return None

        if self.recurrence.endDate is not None and self.recurrence.endDate < entryDate:
            return None
        recurrentOffset: relativedelta = self.recurrence.getDateOffset()
        if recurrentOffset is None:
            return None

        multiplicator = recurrent.findMultiplicationAfter( dateRange.end, entryDate, recurrentOffset )
        if multiplicator < 1:
            return None
        dateRange += recurrentOffset * multiplicator
        if entryDate in dateRange:
            return TaskOccurrence( self, multiplicator )
        return None

    def addReminder( self, reminder=None ):
        if self.reminderList is None:
            self.reminderList = list()
        if reminder is None:
            reminder = Reminder()
        self.reminderList.append( reminder )
        return reminder

    def getReminderFirstDate(self) -> datetime:
        if self.dueDate is None:
            return None
        if self.reminderList is None:
            return None
        retOffset = None
        for reminder in self.reminderList:
            if retOffset is None:
                retOffset = reminder.getOffset()
                continue
            currOffset = reminder.getOffset()
            if currOffset > retOffset:
                retOffset = currOffset
        if retOffset is None:
            return None
        return self.dueDate - retOffset

    def getNotifications(self) -> List[Notification]:
        if self.dueDate is None:
            return list()
        currTime = datetime.today()
        ret: List[Notification] = list()
        if self.dueDate > currTime:
            notif = Notification()
            notif.notifyTime = self.dueDate
            notif.task = self
            notif.message = "task '%s' reached deadline" % self.title
            ret.append( notif )

        if self.reminderList is None:
            return ret

        for reminder in self.reminderList:
            notifTime = self.dueDate - reminder.getOffset()
            if notifTime > currTime:
                notif = Notification()
                notif.notifyTime = notifTime
                notif.task = self
                notif.message = "task '%s': %s" % (self.title, reminder.printPretty())
                ret.append( notif )

        ret.sort( key=Notification.sortByTime )
        return ret

    def isTimedout(self):
        if self.dueDate is None:
            return False
        currTime = datetime.today()
        return currTime > self.dueDate

    def isReminded(self):
        if self.dueDate is None:
            return False
        if self.reminderList is None:
            return False

        currTime = datetime.today()
        for reminder in self.reminderList:
            notifTime = self.dueDate - reminder.getOffset()
            if notifTime < currTime:
                return True
        return False

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

    @staticmethod
    def sortByDates( task ):
        return ( task.dueDate, task.startDate )


class TaskOccurrence:
    """Occurrences of task.

    Regular task has only one occurrence.
    Recurrent tasks has many occurrences.
    """

    def __init__(self, task, offset=0):
        self.task                  = task
        self.offset                = offset
        self._dateRange: DateRange = None           ## cache

    def isValid(self):
        if self.task is None:
            return False
        if self.dateRange is None:
            return False
        return True

    @property
    def title(self):
        return self.task.title

    def isCompleted(self):
        return self.task.isCompleted()

    def isTimedout(self):
        return self.task.isTimedout()

    def isReminded(self):
        return self.task.isReminded()

    @property
    def dateRange(self):
        if hasattr(self, '_dateRange') and self._dateRange is not None:
            return self._dateRange

        if self.task is None:
            self.dateRange = [None, None]
            return self._dateRange
        dateRange: DateRange = self.task.getDateRangeNormalized()
        if dateRange is None:
            self._dateRange = [None, None]
            return self._dateRange
        if self.offset != 0:
            recurrenceOffset = self.task.recurrence.getDateOffset()
            dateRange += recurrenceOffset * self.offset
        self._dateRange = dateRange
        return self._dateRange

    @staticmethod
    def sortByDates( entry ):
        return ( entry.dateRange[1], entry.dateRange[0] )


def calcTimeSpan(entryDate: date, start: datetime, end: datetime):
    startFactor = 0.0
    if start is not None:
        date = start.date()
        if entryDate < date:
            return None
        elif entryDate == date:
            midnight = datetime.combine( entryDate, datetime.min.time() )
            startDiff = start - midnight
            daySecs = timedelta( days=1 ).total_seconds()
            startFactor = startDiff.total_seconds() / timedelta( days=1 ).total_seconds()
    dueFactor = 1.0
    if end is not None:
        date = end.date()
        if entryDate > date:
            return None
        elif entryDate == date:
            midnight = datetime.combine( entryDate, datetime.min.time() )
            startDiff = end - midnight
            daySecs = timedelta( days=1 ).total_seconds()
            dueFactor = startDiff.total_seconds() / daySecs
    ret = [startFactor, dueFactor]
    return ret


def ensureDateTime( value ):
    if value is None:
        return value
    if isinstance( value, datetime):
        return value
    if isinstance( value, date):
        value = datetime.combine( value, datetime.min.time() )
    _LOGGER.warn( "unknown type: %s", value )
    return None
