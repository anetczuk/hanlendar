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

from typing import List
from datetime import date, time, datetime, timedelta
from dateutil.relativedelta import relativedelta

from hanlendar import persist
from hanlendar.domainmodel import recurrent
from hanlendar.domainmodel.recurrent import Recurrent

from .reminder import Reminder, Notification


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
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateRange( start, end )

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

    def isInMonth( self, monthDate: date ):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate.year == monthDate.year and currDate.month == monthDate.month:
            return True
        return False

    def __str__(self):
        return "[s:%s e:%s]" % ( self.start, self.end )


## ========================================================================


class DateTimeRange():

    def __init__(self, start=None, end=None ):
        self.start: datetime = start
        self.end:   datetime = end

    ## [] (array) operator
    def __getitem__(self, arg):
        if arg == 0:
            return self.start
        if arg == 1:
            return self.end
        raise IndexError( "bad index: 0 or 1 allowed" )

    ## + (plus) operator
    def __add__(self, dateOffset):
        start = self.start
        if start is not None:
            start += dateOffset
        end = self.end
        if end is not None:
            end += dateOffset
        return DateTimeRange( start, end )

    ## in keyword
    def __contains__(self, entryDate: datetime):
        if self.start is not None and entryDate < self.start:
            return False
        if self.end is not None and entryDate > self.end:
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

    def isInMonth( self, monthDate: datetime ):
        currDate = self.start
        if currDate is None:
            currDate = self.end
        if currDate.year == monthDate.year and currDate.month == monthDate.month:
            return True
        return False

    def __str__(self):
        return "[s:%s e:%s]" % ( self.start, self.end )


## ========================================================================


class TaskOccurrence:
    """Occurrences of task.

    Regular task has only one occurrence.
    Recurrent tasks has many occurrences.
    """

    def __init__(self, task, offset=0):
        if task is None:
            raise TypeError
        self.task                      = task
        self.offset                    = offset         ## recurrence offset
        self._dateRange: DateTimeRange = None           ## cache

    def isValid(self):
        if self.dateRange is None:
            return False
        return True

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
    def due(self):
        return self.dateRange.end

    def isCompleted(self):
        if self.offset < self.task.recurrentOffset:
            return True
        return self.task.isCompleted()

    def isTimedout(self):
        currTime = datetime.today()
        return currTime > self.dateRange.end

    def isReminded(self):
        return self.task.isReminded()

    @property
    def dateRange(self):
        if hasattr(self, '_dateRange') and self._dateRange is not None:
            return self._dateRange

        dateRange: DateTimeRange = self.task.getDateTimeRange()
        if dateRange is None:
            self._dateRange = DateTimeRange()
            return self._dateRange
        if self.offset != 0:
            recurrenceOffset = self.task.recurrence.getDateOffset()
            dateRange += recurrenceOffset * self.offset
        self._dateRange = dateRange
        return self._dateRange

    def getFirstDateTime(self):
        return self.task.getFirstDateTime()

    def isInMonth( self, monthDate: date ):
        return self.dateRange.isInMonth( monthDate )

    def calculateTimeSpan(self, entryDate: date):
        startDate = self.task.occurrenceStart
        endDate   = self.task.occurrenceDue
        ret = calc_time_span( entryDate, startDate, endDate )
        if ret is not None:
            return ret

        recurrence = self.task.recurrence
        if recurrence is None:
            return [0, 1]
        recurrentOffset: relativedelta = recurrence.getDateOffset()
        if recurrentOffset is None:
            return [0, 1]

        multiplicator = recurrent.find_multiplication_after( endDate.date(), entryDate, recurrentOffset )
        if multiplicator < 0:
            return [0, 1]
        endDate += recurrentOffset * multiplicator
        if startDate is not None:
            startDate += recurrentOffset * multiplicator
        ret = calc_time_span( entryDate, startDate, endDate )
        if ret is not None:
            return ret
        return [0, 1]

    def __str__(self):
        return "[t:%s %s off:%s range:%s]" % ( self.task.title, self.task.occurrenceDue, self.offset, self.dateRange )

    @staticmethod
    def sortByDates( entry ):
        return ( entry.dateRange[1], entry.dateRange[0] )


## ========================================================================


class Task( persist.Versionable ):
    """Task is entity that lasts over time."""

    ## 1: _recurrentStartDate and _recurrentDueDate replaced with _recurrentOffset
    _class_version = 1

    def __init__(self, title="" ):
        self.title                          = title
        self.description                    = ""
        self._completed                     = 0        ## in range [0..100]
        self.priority                       = 10       ## lower number, greater priority
        self._startDate: datetime           = None
        self._dueDate: datetime             = None
        self.reminderList: List[Reminder]   = None
        self._recurrence: Recurrent         = None
        self._recurrentOffset               = 0

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            # pylint: disable=W0201
            self.__dict__ = dict_
            return

        if dictVersion_ < 1:
            ## replace _recurrentStartDate and _recurrentDueDate with _recurrentOffset
            self.title                          = dict_["title"]
            self.description                    = dict_["description"]
            self._completed                     = dict_["_completed"]
            self.priority                       = dict_["priority"]
            self._startDate: datetime           = dict_["_startDate"]
            self._dueDate: datetime             = dict_["_dueDate"]
            self.reminderList: List[Reminder]   = dict_["reminderList"]
            self._recurrence: Recurrent         = dict_["_recurrence"]
            self._recurrentOffset               = 0                       ## set default value

            if self._recurrence is not None:
                dueDate = self._dueDate.date()
                targetDueDate = dict_["_recurrentDueDate"].date()
                self._recurrentOffset = self._recurrence.findRecurrentOffset( dueDate, targetDueDate )
            return

        # pylint: disable=W0201
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
        #TODO: return False in case recurrent task when not passed end date
        return self._completed >= 100

    @property
    def startDateTime(self):
        return self._startDate

    @startDateTime.setter
    def startDateTime(self, value):
        value = ensure_date_time( value )
        self._startDate = value
        if self._recurrence is not None:
            self._recurrentOffset = 0

    @property
    def occurrenceStart(self):
        recurrenceDate = self._getRecurrenceDate( self._startDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return self._startDate

    @occurrenceStart.setter
    def occurrenceStart(self, value):
        if self._recurrence is None:
            self._startDate = value
            return
        self._startDate = value - self._recurrence.getDateOffset() * self._recurrentOffset

    @property
    def dueDateTime(self):
        return self._dueDate

    @dueDateTime.setter
    def dueDateTime(self, value):
        value = ensure_date_time( value )
        self._dueDate = value
        if self._recurrence is not None:
            self._recurrentOffset = 0

    @property
    def occurrenceDue(self):
        recurrenceDate = self._getRecurrenceDate( self._dueDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return self._dueDate

    @occurrenceDue.setter
    def occurrenceDue(self, value):
        if self._recurrence is None:
            self._dueDate = value
            return
        self._dueDate = value - self._recurrence.getDateOffset() * self._recurrentOffset

    def currentOccurrence(self) -> TaskOccurrence:
        return TaskOccurrence( self, self._recurrentOffset )

    @property
    def recurrence(self) -> Recurrent:
        return self._recurrence

    @recurrence.setter
    def recurrence(self, value):
        if self._recurrence is None and value is not None:
            self._recurrentOffset = 0
        self._recurrence = value

    @property
    def recurrentOffset(self):
        return self._recurrentOffset

    def getReferenceInitDateTime(self) -> datetime:
        if self._startDate is not None:
            return self._startDate
        ## deadline case
        return self._dueDate

    def getReferenceDateTime(self) -> datetime:
        if self.occurrenceStart is not None:
            return self.occurrenceStart
        ## deadline case
        return self.occurrenceDue

    def getFirstDateTime(self) -> datetime:
        if self.occurrenceDue is None:
            return None
        minDate = self.occurrenceDue
        if self.occurrenceStart is not None and self.occurrenceStart < minDate:
            minDate = self.occurrenceStart
        remindDate = self.getReminderFirstDate()
        if remindDate is not None and remindDate < minDate:
            minDate = remindDate
        return minDate

    def getDateRange(self) -> DateRange:
        startDate = None
        endDate   = None
        if self._startDate is not None:
            startDate = self._startDate.date()
        if self._dueDate is not None:
            endDate = self._dueDate.date()
        return DateRange(startDate, endDate)

    def getDateRangeNormalized(self) -> DateRange:
        dateRange: DateRange = self.getDateRange()
        dateRange.normalize()
        if dateRange[1] is None:
            return None
        return dateRange

    def getDateTimeRange(self) -> DateTimeRange:
        startDate = None
        endDate   = None
        if self._startDate is not None:
            startDate = self._startDate
        if self._dueDate is not None:
            endDate = self._dueDate
        return DateTimeRange(startDate, endDate)

    def getDateTimeRangeNormalized(self) -> DateTimeRange:
        dateRange: DateTimeRange = self.getDateTimeRange()
        dateRange.normalize()
        if dateRange[1] is None:
            return None
        return dateRange

    def setDefaultDateTime(self, start: datetime ):
        self.startDateTime = start
        self.dueDateTime = self.startDateTime + timedelta( hours=1 )

    def setDefaultDate(self, startDate: date):
        start = datetime.combine( startDate, time(10, 0, 0) )
        self.setDefaultDateTime( start )

    def setDeadline(self):
        self.startDateTime = None

    def setDeadlineDateTime(self, due: datetime ):
        self.startDateTime = None
        self.dueDateTime = due

    def setDeadlineDate(self, dueDate: date):
        due = datetime.combine( dueDate, time(10, 0, 0) )
        self.setDeadlineDateTime( due )

    def hasTaskOccurrenceInMonth( self, month: date ):
        refDate = self.getReferenceInitDateTime()
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

        multiplicator = recurrent.find_multiplication_after( dateRange.end, entryDate, recurrentOffset )
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
        if self.occurrenceDue is None:
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
        return self.occurrenceDue - retOffset

    def getNotifications(self) -> List[Notification]:
        if self.occurrenceDue is None:
            return list()
        currTime = datetime.today()
        ret: List[Notification] = list()
        if self.occurrenceDue > currTime:
            notif = Notification()
            notif.notifyTime = self.occurrenceDue
            notif.task = self
            notif.message = "task '%s' reached deadline" % self.title
            ret.append( notif )

        if self.reminderList is None:
            return ret

        for reminder in self.reminderList:
            notifTime = self.occurrenceDue - reminder.getOffset()
            if notifTime > currTime:
                notif = Notification()
                notif.notifyTime = notifTime
                notif.task = self
                notif.message = "task '%s': %s" % (self.title, reminder.printPretty())
                ret.append( notif )

        ret.sort( key=Notification.sortByTime )
        return ret

    def isTimedout(self):
        if self.occurrenceDue is None:
            return False
        currTime = datetime.today()
        return currTime > self.occurrenceDue

    def isReminded(self):
        if self.occurrenceDue is None:
            return False
        if self.reminderList is None:
            return False

        currTime = datetime.today()
        for reminder in self.reminderList:
            notifTime = self.occurrenceDue - reminder.getOffset()
            if notifTime < currTime:
                return True
        return False

    def printNextRecurrence(self) -> str:
        if self._recurrence is None:
            return "None"
        refDate = self.getReferenceDateTime()
        nextRepeat = self._recurrence.nextDateTime( refDate )
        if nextRepeat is None:
            return "None"
        dateText = nextRepeat.strftime( "%Y-%m-%d %H:%M" )
        return dateText

    def __str__(self):
        return "[t:%s d:%s c:%s p:%s sd:%s dd:%s rem:%s rec:%s ro:%s]" % (
            self.title, self.description, self._completed, self.priority,
            self.occurrenceStart, self.occurrenceDue,
            self.reminderList, self._recurrence,
            self._recurrentOffset )

    def _progressRecurrence(self) -> bool:
        if self._recurrence is None:
            return False
        nextDueDate = self._getRecurrenceDate( self._dueDate, 1 )
        if self._recurrence.isEnd( nextDueDate ):
            return False
        self._recurrentOffset += 1
        return True

    def _getRecurrenceDate(self, aDate: date, offset: int = 0):
        if aDate is None:
            return None
        if self._recurrence is None:
            return None
        recurrentDate = aDate + self._recurrence.getDateOffset() * (self._recurrentOffset + offset)
        return recurrentDate

    @staticmethod
    def sortByDates( task ):
        return ( task.occurrenceDue, task.occurrenceStart )


def calc_time_span(entryDate: date, start: datetime, end: datetime):
    startFactor = 0.0
    if start is not None:
        startDate = start.date()
        if entryDate < startDate:
            return None
        elif entryDate == startDate:
            midnight = datetime.combine( entryDate, datetime.min.time() )
            startDiff = start - midnight
            daySecs = timedelta( days=1 ).total_seconds()
            startFactor = startDiff.total_seconds() / timedelta( days=1 ).total_seconds()
    dueFactor = 1.0
    if end is not None:
        endDate = end.date()
        if entryDate > endDate:
            return None
        elif entryDate == endDate:
            midnight = datetime.combine( entryDate, datetime.min.time() )
            startDiff = end - midnight
            daySecs = timedelta( days=1 ).total_seconds()
            dueFactor = startDiff.total_seconds() / daySecs
    ret = [startFactor, dueFactor]
    return ret


def ensure_date_time( value ):
    if value is None:
        return value
    if isinstance( value, datetime):
        return value
    if isinstance( value, date):
        value = datetime.combine( value, datetime.min.time() )
    _LOGGER.warning( "unknown type: %s", value )
    return None
