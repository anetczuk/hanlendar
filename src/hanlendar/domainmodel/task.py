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
from hanlendar.domainmodel.item import Item

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
        if currDate is None:
            return False
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
        if self.dateRange.end is None:
            return False
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
            recurrenceOffset = self.task.getAppliedRecurrence().getDateOffset()
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

        recurrence = self.task.getAppliedRecurrence()
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


class Task( Item, persist.Versionable ):
    """Task is entity that lasts over time."""

    ## 1: _recurrentStartDate and _recurrentDueDate replaced with _recurrentOffset
    ## 2: add base class Item
    _class_version = 2

    def __init__(self, title="" ):
        super(Task, self).__init__( title )
        self._startDate: datetime           = None
        self._dueDate: datetime             = None
        self.reminderList: List[Reminder]   = None
        self._recurrence: Recurrent         = None
        self._recurrentOffset               = 0

    def _convertstate_(self, dict_, dictVersion_ ):
        _LOGGER.info( "converting object from version %s to %s", dictVersion_, self._class_version )

        if dictVersion_ is None:
            dictVersion_ = -1

        if dictVersion_ < 0:
            ## do nothing
            dictVersion_ = 0

        if dictVersion_ == 0:
            ## replace _recurrentStartDate and _recurrentDueDate with _recurrentOffset
            recurrence = dict_["_recurrence"]
            if recurrence is not None:
                dueDate = dict_["_dueDate"].date()
                targetDueDate = dict_["_recurrentDueDate"].date()
                recurrentOffset = recurrence.findRecurrentOffset( dueDate, targetDueDate )
                dict_["_recurrentOffset"] = recurrentOffset
            else:
                ## set default value
                dict_["_recurrentOffset"] = 0
            dictVersion_ = 1

        if dictVersion_ == 1:
            ## add field
            dict_["subitems"] = None
            dictVersion_ = 2

        # pylint: disable=W0201
        self.__dict__ = dict_

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

    @property
    def startDateTime(self):
        return self._startDate

    @startDateTime.setter
    def startDateTime(self, value):
        value = ensure_date_time( value )
        self._startDate = value
        self._recurrentOffset = 0

    @property
    def occurrenceStart(self):
        recurrenceDate = self._getRecurrenceDate( self._startDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return self._startDate

    @occurrenceStart.setter
    def occurrenceStart(self, value):
        relativeDate = self._getRecurrenceRelative()
        if relativeDate is None:
            self._startDate = value
            return
        self._startDate = value - relativeDate

    @property
    def dueDateTime(self):
        return self._dueDate

    @dueDateTime.setter
    def dueDateTime(self, value):
        value = ensure_date_time( value )
        self._dueDate = value
        self._recurrentOffset = 0

    @property
    def occurrenceDue(self):
        recurrenceDate = self._getRecurrenceDate( self._dueDate )
        if recurrenceDate is not None:
            return recurrenceDate
        return self._dueDate

    @occurrenceDue.setter
    def occurrenceDue(self, value):
        relativeDate = self._getRecurrenceRelative()
        if relativeDate is None:
            self._dueDate = value
            return
        self._dueDate = value - relativeDate

    def currentOccurrence(self) -> TaskOccurrence:
        return TaskOccurrence( self, self._recurrentOffset )

    ## =====================================================================

    @property
    def recurrence(self) -> Recurrent:
        return self._recurrence

    @recurrence.setter
    def recurrence(self, value):
        if self._recurrence is None and value is not None:
            self._recurrentOffset = 0
        self._recurrence = value

    def getAppliedRecurrence(self) -> Recurrent:
        if self._recurrence is None:
            return None
        if self._recurrence.isAsParent() is False:
            return self._recurrence
        if self.parent is None:
            return None
        return self.parent.getAppliedRecurrence()

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
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return False
        return recurr.hasTaskOccurrenceInMonth( currDate, month )

    def getTaskOccurrenceForDate(self, entryDate: date):
        dateRange: DateRange = self.getDateRangeNormalized()
        if dateRange is None:
            return None
        if entryDate in dateRange:
            return TaskOccurrence( self )

        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return None

        if recurr.endDate is not None and recurr.endDate < entryDate:
            return None
        recurrentOffset: relativedelta = recurr.getDateOffset()
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
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return "None"
        refDate = self.getReferenceDateTime()
        nextRepeat = recurr.nextDateTime( refDate )
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
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return False
        nextDueDate = self._getRecurrenceDate( self._dueDate, 1 )
        nextDate = nextDueDate.date()
        if recurr.isEnd( nextDate ):
            return False
        self._recurrentOffset += 1
        return True

    def _getRecurrenceDate(self, aDate: datetime, offset: int = 0) -> datetime:
        if aDate is None:
            return None
        relativeDate = self._getRecurrenceRelative( offset )
        if relativeDate is None:
            return None
        recurrentDate = aDate + relativeDate
        return recurrentDate

    def _getRecurrenceRelative(self, offset: int = 0) -> relativedelta:
        recurr = self.getAppliedRecurrence()
        if recurr is None:
            return None
        return recurr.getDateOffset() * (self._recurrentOffset + offset)

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
    _LOGGER.warning( "unknown type: %s %s", value, type(value) )
    return None
